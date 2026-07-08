"""Cart & checkout application services."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Sum

from apps.catalog.models import ProductStatus, ProductVariant
from apps.core.exceptions import (
    BusinessRuleError,
    ConflictError,
    ValidationError,
)
from apps.core.services import BaseService, atomic
from apps.core.signals import (
    order_cancelled,
    order_confirmed,
    order_placed,
    order_status_changed,
)
from apps.inventory.models import ReservationStatus, StockItem, StockReservation
from apps.inventory.services import InventoryService
from apps.orders.models import (
    FULFILLMENT_NEXT,
    Cart,
    CartItem,
    CartStatus,
    Order,
    OrderEvent,
    OrderItem,
    OrderStatus,
)

_CENTS = Decimal("0.01")


def _money(value) -> Decimal:
    return Decimal(value).quantize(_CENTS, rounding=ROUND_HALF_UP)


def _available_for(variant) -> int:
    from apps.catalog.models import COMPOSITE_KINDS, ProductType

    product = variant.product
    # Bundles/kits/composites have no stock of their own; availability is the
    # most constraining required component.
    if product.kind in COMPOSITE_KINDS:
        components = list(
            product.components.filter(is_optional=False).select_related("component_variant")
        )
        if not components:
            return 0
        return min(_available_for(c.component_variant) // c.quantity for c in components)
    # Digital goods are not stock-limited, unless gated by a finite license-key pool.
    if product.product_type == ProductType.DIGITAL:
        from apps.catalog.models import DigitalAsset, LicenseKey, LicenseKeyStatus

        asset = DigitalAsset.objects.filter(variant=variant, is_active=True).first()
        if asset is not None and asset.requires_license:
            return LicenseKey.objects.filter(
                variant=variant, status=LicenseKeyStatus.AVAILABLE
            ).count()
        return 1_000_000
    agg = StockItem.objects.filter(variant=variant).aggregate(
        on_hand=Sum("quantity"), reserved=Sum("reserved_quantity")
    )
    return max((agg["on_hand"] or 0) - (agg["reserved"] or 0), 0)


class CartService(BaseService):
    def get_active_cart(self, *, store, user) -> Cart:
        cart, _ = Cart.objects.get_or_create(store=store, user=user, status=CartStatus.ACTIVE)
        return cart

    def read_cart(self, *, store, user) -> Cart:
        """The active cart with items prefetched for serialization (avoids N+1)."""
        cart = self.get_active_cart(store=store, user=user)
        return Cart.objects.prefetch_related("items__variant__product").filter(pk=cart.pk).first()

    def _purchasable_variant(self, variant_id) -> ProductVariant:
        variant = (
            ProductVariant.objects.filter(id=variant_id, is_active=True)
            .select_related("product")
            .first()
        )
        if variant is None:
            raise ValidationError(
                "This product variant is not available.",
                code="variant_unavailable",
                errors={"variant_id": ["Not available in this store."]},
            )
        if variant.product.status != ProductStatus.PUBLISHED:
            raise BusinessRuleError(
                "This product is not available for purchase.", code="not_purchasable"
            )
        return variant

    @atomic
    def add_item(self, *, store, user, variant_id, quantity: int) -> CartItem:
        if quantity <= 0:
            raise ValidationError("Quantity must be positive.")
        variant = self._purchasable_variant(variant_id)
        cart = self.get_active_cart(store=store, user=user)
        existing = cart.items.filter(variant=variant).first()
        desired = quantity + (existing.quantity if existing else 0)
        if _available_for(variant) < desired:
            raise BusinessRuleError("Insufficient stock available.", code="insufficient_stock")
        unit_price = self._resolve_price(store=store, variant=variant, user=user, quantity=desired)
        if existing is not None:
            existing.quantity = desired
            existing.unit_price = unit_price
            existing.save(update_fields=["quantity", "unit_price", "updated_at"])
            return existing
        return CartItem.objects.create(
            store=store,
            cart=cart,
            variant=variant,
            quantity=quantity,
            unit_price=unit_price,
        )

    @atomic
    def update_item(self, *, item: CartItem, quantity: int) -> CartItem | None:
        if quantity <= 0:
            item.delete()
            return None
        if _available_for(item.variant) < quantity:
            raise BusinessRuleError("Insufficient stock available.", code="insufficient_stock")
        item.quantity = quantity
        item.unit_price = self._resolve_price(
            store=item.store, variant=item.variant, user=item.cart.user, quantity=quantity
        )
        item.save(update_fields=["quantity", "unit_price", "updated_at"])
        return item

    def remove_item(self, *, item: CartItem) -> None:
        item.delete()

    def clear(self, *, cart: Cart) -> None:
        cart.items.all().delete()

    @staticmethod
    def _resolve_price(*, store, variant, user, quantity: int):
        # Effective price from the pricing engine (group/tier/dynamic rules).
        # Falls back to the variant's base price when no rule applies.
        from apps.pricing.services import PricingService

        return PricingService().resolve_price(
            store=store, variant=variant, user=user, quantity=quantity
        )

    def apply_coupon(self, *, store, user, code: str) -> Cart:
        from apps.promotions.services import PromotionService

        cart = self.get_active_cart(store=store, user=user)
        # Validate against the current subtotal (raises if not applicable).
        PromotionService().validate(store=store, code=code, user=user, subtotal=cart.subtotal)
        cart.coupon_code = code.strip().upper()
        cart.save(update_fields=["coupon_code", "updated_at"])
        return cart

    def remove_coupon(self, *, store, user) -> Cart:
        cart = self.get_active_cart(store=store, user=user)
        cart.coupon_code = ""
        cart.save(update_fields=["coupon_code", "updated_at"])
        return cart


class CheckoutService(BaseService):
    def __init__(self, inventory: InventoryService | None = None) -> None:
        self.inventory = inventory or InventoryService()

    @atomic
    def checkout(
        self,
        *,
        store,
        user,
        shipping_method_id=None,
        country=None,
        currency=None,
        address_id=None,
    ) -> Order:
        cart = (
            Cart.objects.filter(store=store, user=user, status=CartStatus.ACTIVE)
            .prefetch_related("items__variant__product")
            .first()
        )
        items = list(cart.items.select_related("variant__product")) if cart else []
        if not items:
            raise ValidationError("Your cart is empty.", code="empty_cart")

        # Optional shipping address: snapshot it and let it drive the destination
        # country (overriding the explicit country arg). No address -> unchanged.
        shipping_address, address_country = self._resolve_address(
            store=store, user=user, address_id=address_id
        )
        country = address_country or country

        priced = self._price_cart(
            store=store,
            user=user,
            cart=cart,
            items=items,
            shipping_method_id=shipping_method_id,
            country=country,
            currency=currency,
        )
        coupon, coupon_discount = priced["coupon"], priced["coupon_discount"]
        method, order_currency, fx = priced["method"], priced["currency"], priced["fx"]

        order = Order.objects.create(
            store=store,
            user=user,
            number=self._generate_number(store),
            currency=order_currency,
            subtotal=fx(priced["subtotal"]),
            discount_total=fx(priced["discount"]),
            tax_total=fx(priced["tax_total"]),
            shipping_total=fx(priced["shipping_total"]),
            total=fx(priced["total"]),
            coupon_code=coupon.code if coupon else "",
            shipping_method=method.name if method else "",
            shipping_address=shipping_address,
            status=OrderStatus.PENDING,
        )
        reference = f"order:{order.id}"
        for item in items:
            OrderItem.objects.create(
                store=store,
                order=order,
                variant=item.variant,
                product_name=item.variant.product.name,
                sku=item.variant.sku,
                unit_price=fx(item.unit_price),
                quantity=item.quantity,
                line_total=fx(item.line_total),
            )
            self._reserve_for_item(
                store=store, variant=item.variant, quantity=item.quantity, reference=reference
            )

        if coupon is not None:
            from apps.promotions.services import PromotionService

            PromotionService().redeem(
                store=store, coupon=coupon, user=user, order=order, amount=coupon_discount
            )

        cart.status = CartStatus.CHECKED_OUT
        cart.save(update_fields=["status", "updated_at"])
        self._record_event(order, OrderStatus.PENDING, "Order placed")
        order_placed.send(sender=self.__class__, order=order)
        return order

    def _price_cart(self, *, store, user, cart, items, shipping_method_id, country, currency):
        """Compute the full money breakdown for a cart. The single source of truth
        shared by ``checkout`` (persisted) and ``quote`` (preview), so the total a
        buyer sees at checkout always matches the order that gets placed."""
        subtotal = _money(sum((i.line_total for i in items), Decimal("0.00")))
        coupon, coupon_discount = self._resolve_discount(
            store=store, user=user, code=cart.coupon_code, subtotal=subtotal
        )
        # Automatic campaigns (flash sales, BXGY, order discounts, free shipping).
        promo = self._auto_promotions(store=store, items=items, subtotal=subtotal)
        discount = _money(min(coupon_discount + promo.discount, subtotal))
        taxable = subtotal - discount
        # Destination-based tax: shipping country, then the store's own country.
        tax_total, taxed_total = self._totals(
            store=store, amount=taxable, country=country or store.country or None
        )
        weight = sum(
            (Decimal(str(item.variant.weight or 0)) * item.quantity for item in items),
            Decimal("0"),
        )
        method, shipping_total = self._shipping(
            store=store, method_id=shipping_method_id, country=country, subtotal=subtotal, weight=weight
        )
        if promo.free_shipping:
            shipping_total = Decimal("0.00")
        total = _money(taxed_total + shipping_total)
        order_currency, fx = self._resolve_currency(store=store, currency=currency)
        return {
            "subtotal": subtotal,
            "discount": discount,
            "tax_total": tax_total,
            "shipping_total": shipping_total,
            "total": total,
            "coupon": coupon,
            "coupon_discount": coupon_discount,
            "method": method,
            "currency": order_currency,
            "fx": fx,
        }

    def quote(self, *, store, user, shipping_method_id=None, country=None, currency=None, address_id=None) -> dict:
        """Preview the checkout totals (incl. tax + shipping) without placing the
        order, so the summary shown to the buyer is the real, final amount."""
        cart = (
            Cart.objects.filter(store=store, user=user, status=CartStatus.ACTIVE)
            .prefetch_related("items__variant__product")
            .first()
        )
        items = list(cart.items.select_related("variant__product")) if cart else []
        order_currency, _ = self._resolve_currency(store=store, currency=currency)
        empty = {
            "currency": order_currency,
            "subtotal": "0.00",
            "discount": "0.00",
            "tax": "0.00",
            "shipping": "0.00",
            "total": "0.00",
            "shipping_method": None,
        }
        if not items:
            return empty
        _shipping_address, address_country = self._resolve_address(
            store=store, user=user, address_id=address_id
        )
        country = address_country or country
        priced = self._price_cart(
            store=store,
            user=user,
            cart=cart,
            items=items,
            shipping_method_id=shipping_method_id,
            country=country,
            currency=currency,
        )
        fx = priced["fx"]
        return {
            "currency": priced["currency"],
            "subtotal": str(fx(priced["subtotal"])),
            "discount": str(fx(priced["discount"])),
            "tax": str(fx(priced["tax_total"])),
            "shipping": str(fx(priced["shipping_total"])),
            "total": str(fx(priced["total"])),
            "shipping_method": priced["method"].name if priced["method"] else None,
        }

    @atomic
    def confirm_order(self, *, order: Order) -> Order:
        if order.status != OrderStatus.PENDING:
            raise ConflictError("Only a pending order can be confirmed.")
        self._assert_fraud_cleared(order)
        for reservation in self._active_reservations(order):
            self.inventory.commit(reservation=reservation)
        order.status = OrderStatus.CONFIRMED
        order.save(update_fields=["status", "updated_at"])
        # Fulfil any digital items (assign license keys + create download grants).
        # No-op for orders without digital products.
        from apps.catalog.services import DigitalFulfillmentService

        DigitalFulfillmentService().fulfill(order=order)
        # Award loyalty points (no-op when the store's earn rate is 0).
        from apps.rewards.services import LoyaltyService

        LoyaltyService().earn_for_order(order=order)
        self._record_event(order, OrderStatus.CONFIRMED)
        order_confirmed.send(sender=self.__class__, order=order)
        return order

    @atomic
    def cancel_order(self, *, order: Order) -> Order:
        if order.status == OrderStatus.CANCELLED:
            return order
        if order.status == OrderStatus.CONFIRMED:
            raise ConflictError("A confirmed order cannot be cancelled here.")
        for reservation in self._active_reservations(order):
            self.inventory.release(reservation=reservation)
        order.status = OrderStatus.CANCELLED
        order.save(update_fields=["status", "updated_at"])
        self._record_event(order, OrderStatus.CANCELLED)
        order_cancelled.send(sender=self.__class__, order=order)
        return order

    @atomic
    def advance_status(self, *, order: Order, status, note: str = "", tracking_number=None, carrier=None) -> Order:
        """Move an order along the fulfillment flow (processing → shipped → out for
        delivery → delivered), recording a tracking event the customer can follow."""
        try:
            new_status = OrderStatus(status)
        except ValueError as exc:
            raise ValidationError("Unknown order status.", code="invalid_status") from exc
        if new_status not in FULFILLMENT_NEXT.get(order.status, set()):
            raise ConflictError(
                f"An order can't move from '{order.status}' to '{new_status}'.",
                code="invalid_transition",
            )
        fields = ["status", "updated_at"]
        order.status = new_status
        if tracking_number is not None:
            order.tracking_number = tracking_number
            fields.append("tracking_number")
        if carrier is not None:
            order.carrier = carrier
            fields.append("carrier")
        order.save(update_fields=fields)
        self._record_event(order, new_status, note)
        order_status_changed.send(sender=self.__class__, order=order, status=new_status)
        return order

    @staticmethod
    def _record_event(order: Order, status, note: str = "") -> None:
        OrderEvent.objects.create(store=order.store, order=order, status=status, note=note or "")

    # --- Helpers ---
    def _resolve_discount(self, *, store, user, code: str, subtotal: Decimal):
        """Re-validate the cart's coupon at checkout; return (coupon|None, discount)."""
        if not code:
            return None, Decimal("0.00")
        from apps.promotions.services import PromotionService

        service = PromotionService()
        coupon = service.validate(store=store, code=code, user=user, subtotal=subtotal)
        return coupon, service.compute_discount(coupon=coupon, subtotal=subtotal)

    @staticmethod
    def _tax_rate(store, country=None) -> Decimal:
        # Tax engine (zones/rates by destination country); falls back to the
        # store's flat default_tax_rate when no zone matches.
        from apps.finance.services import TaxService

        return TaxService().resolve_rate(store=store, country=country or store.country or None)

    @staticmethod
    def _resolve_currency(*, store, currency):
        """Return (currency_code, convert_fn) for the order's settlement currency.

        With no selection (or the store's own currency) this is the identity, so
        orders settle in the store currency exactly as before.
        """
        target = (currency or "").strip().upper()
        if not target or target == store.currency:
            return store.currency, _money
        from apps.finance.services import CurrencyService

        service = CurrencyService()

        def convert(amount):
            return service.convert(
                store=store, amount=amount, base_code=store.currency, target_code=target
            )

        return target, convert

    @staticmethod
    def _assert_fraud_cleared(order: Order) -> None:
        # Block confirmation while a fraud check holds the order. No-op when the
        # fraud app isn't installed or the order was approved.
        from apps.fraud.services import FraudService

        if FraudService().is_blocked(order=order):
            raise BusinessRuleError(
                "This order is on hold pending fraud review.", code="order_on_hold"
            )

    @staticmethod
    def _resolve_address(*, store, user, address_id):
        """Return (snapshot_dict, country) for a chosen address, else ({}, None)."""
        if not address_id:
            return {}, None
        from apps.addresses.services import AddressService

        address = AddressService().get_for_user(store=store, user=user, address_id=address_id)
        return address.snapshot(), address.country or None

    @staticmethod
    def _auto_promotions(*, store, items, subtotal):
        # Evaluate automatic campaigns. Lazy import avoids an orders<->promotions cycle.
        from apps.promotions.engine import PromotionEngine

        return PromotionEngine().evaluate(store=store, items=items, subtotal=subtotal)

    @staticmethod
    def _shipping(*, store, method_id, country, subtotal, weight):
        # Returns (method|None, shipping_total). No method selected -> free/0.
        if not method_id:
            return None, Decimal("0.00")
        from apps.shipping.services import ShippingService

        return ShippingService().compute(
            store=store,
            method_id=method_id,
            country=country or store.country or None,
            subtotal=subtotal,
            weight=weight,
        )

    def _totals(self, *, store, amount: Decimal, country=None) -> tuple[Decimal, Decimal]:
        """Return (tax_total, total) for a taxable ``amount`` (subtotal - discount)."""
        rate = self._tax_rate(store, country)
        if store.settings.tax_inclusive_pricing:
            divisor = Decimal("1") + rate / Decimal("100")
            net = amount / divisor if divisor else amount
            return _money(amount - net), _money(amount)
        tax = amount * rate / Decimal("100")
        return _money(tax), _money(amount + tax)

    def _reserve_for_item(self, *, store, variant, quantity: int, reference: str) -> None:
        """Reserve stock for a cart line: components for composites, else the variant."""
        from apps.catalog.models import COMPOSITE_KINDS, ProductType

        product = variant.product
        if product.product_type == ProductType.DIGITAL:
            return  # digital goods hold no physical stock
        if product.kind in COMPOSITE_KINDS:
            for component in product.components.filter(is_optional=False).select_related(
                "component_variant"
            ):
                self._reserve(
                    store=store,
                    variant=component.component_variant,
                    quantity=quantity * component.quantity,
                    reference=reference,
                )
        else:
            self._reserve(store=store, variant=variant, quantity=quantity, reference=reference)

    def _reserve(self, *, store, variant, quantity: int, reference: str) -> None:
        needed = quantity
        candidates = sorted(
            StockItem.objects.filter(variant=variant).select_related("warehouse"),
            key=lambda s: s.available_quantity,
            reverse=True,
        )
        for stock in candidates:
            if needed <= 0:
                break
            take = min(stock.available_quantity, needed)
            if take <= 0:
                continue
            self.inventory.reserve(
                store=store,
                variant=variant,
                warehouse=stock.warehouse,
                quantity=take,
                reference=reference,
            )
            needed -= take
        if needed > 0:
            raise BusinessRuleError(
                "Insufficient stock to fulfil the order.", code="insufficient_stock"
            )

    @staticmethod
    def _active_reservations(order: Order):
        return StockReservation.objects.filter(
            reference=f"order:{order.id}", status=ReservationStatus.ACTIVE
        )

    @staticmethod
    def _generate_number(store) -> str:
        prefix = store.settings.order_number_prefix or "ORD"
        sequence = Order.all_objects.filter(store=store).count() + 1
        return f"{prefix}-{sequence:06d}"
