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
from apps.inventory.models import ReservationStatus, StockItem, StockReservation
from apps.inventory.services import InventoryService
from apps.orders.models import (
    Cart,
    CartItem,
    CartStatus,
    Order,
    OrderItem,
    OrderStatus,
)

_CENTS = Decimal("0.01")


def _money(value) -> Decimal:
    return Decimal(value).quantize(_CENTS, rounding=ROUND_HALF_UP)


def _available_for(variant) -> int:
    from apps.catalog.models import COMPOSITE_KINDS

    # Bundles/kits/composites have no stock of their own; availability is the
    # most constraining required component.
    if variant.product.kind in COMPOSITE_KINDS:
        components = list(
            variant.product.components.filter(is_optional=False).select_related("component_variant")
        )
        if not components:
            return 0
        return min(_available_for(c.component_variant) // c.quantity for c in components)
    agg = StockItem.objects.filter(variant=variant).aggregate(
        on_hand=Sum("quantity"), reserved=Sum("reserved_quantity")
    )
    return max((agg["on_hand"] or 0) - (agg["reserved"] or 0), 0)


class CartService(BaseService):
    def get_active_cart(self, *, store, user) -> Cart:
        cart, _ = Cart.objects.get_or_create(store=store, user=user, status=CartStatus.ACTIVE)
        return cart

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
        if existing is not None:
            existing.quantity = desired
            existing.unit_price = variant.price
            existing.save(update_fields=["quantity", "unit_price", "updated_at"])
            return existing
        return CartItem.objects.create(
            store=store,
            cart=cart,
            variant=variant,
            quantity=quantity,
            unit_price=variant.price,
        )

    @atomic
    def update_item(self, *, item: CartItem, quantity: int) -> CartItem | None:
        if quantity <= 0:
            item.delete()
            return None
        if _available_for(item.variant) < quantity:
            raise BusinessRuleError("Insufficient stock available.", code="insufficient_stock")
        item.quantity = quantity
        item.save(update_fields=["quantity", "updated_at"])
        return item

    def remove_item(self, *, item: CartItem) -> None:
        item.delete()

    def clear(self, *, cart: Cart) -> None:
        cart.items.all().delete()

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
    def checkout(self, *, store, user) -> Order:
        cart = (
            Cart.objects.filter(store=store, user=user, status=CartStatus.ACTIVE)
            .prefetch_related("items__variant__product")
            .first()
        )
        items = list(cart.items.select_related("variant__product")) if cart else []
        if not items:
            raise ValidationError("Your cart is empty.", code="empty_cart")

        subtotal = _money(sum((i.line_total for i in items), Decimal("0.00")))
        coupon, discount = self._resolve_discount(
            store=store, user=user, code=cart.coupon_code, subtotal=subtotal
        )
        taxable = subtotal - discount
        tax_total, total = self._totals(store=store, amount=taxable)

        order = Order.objects.create(
            store=store,
            user=user,
            number=self._generate_number(store),
            currency=store.currency,
            subtotal=subtotal,
            discount_total=discount,
            tax_total=tax_total,
            total=total,
            coupon_code=coupon.code if coupon else "",
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
                unit_price=item.unit_price,
                quantity=item.quantity,
                line_total=_money(item.line_total),
            )
            self._reserve_for_item(
                store=store, variant=item.variant, quantity=item.quantity, reference=reference
            )

        if coupon is not None:
            from apps.promotions.services import PromotionService

            PromotionService().redeem(
                store=store, coupon=coupon, user=user, order=order, amount=discount
            )

        cart.status = CartStatus.CHECKED_OUT
        cart.save(update_fields=["status", "updated_at"])
        return order

    @atomic
    def confirm_order(self, *, order: Order) -> Order:
        if order.status != OrderStatus.PENDING:
            raise ConflictError("Only a pending order can be confirmed.")
        for reservation in self._active_reservations(order):
            self.inventory.commit(reservation=reservation)
        order.status = OrderStatus.CONFIRMED
        order.save(update_fields=["status", "updated_at"])
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
        return order

    # --- Helpers ---
    def _resolve_discount(self, *, store, user, code: str, subtotal: Decimal):
        """Re-validate the cart's coupon at checkout; return (coupon|None, discount)."""
        if not code:
            return None, Decimal("0.00")
        from apps.promotions.services import PromotionService

        service = PromotionService()
        coupon = service.validate(store=store, code=code, user=user, subtotal=subtotal)
        return coupon, service.compute_discount(coupon=coupon, subtotal=subtotal)

    def _totals(self, *, store, amount: Decimal) -> tuple[Decimal, Decimal]:
        """Return (tax_total, total) for a taxable ``amount`` (subtotal - discount)."""
        rate = store.settings.default_tax_rate or Decimal("0")
        if store.settings.tax_inclusive_pricing:
            divisor = Decimal("1") + rate / Decimal("100")
            net = amount / divisor if divisor else amount
            return _money(amount - net), _money(amount)
        tax = amount * rate / Decimal("100")
        return _money(tax), _money(amount + tax)

    def _reserve_for_item(self, *, store, variant, quantity: int, reference: str) -> None:
        """Reserve stock for a cart line: components for composites, else the variant."""
        from apps.catalog.models import COMPOSITE_KINDS

        product = variant.product
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
