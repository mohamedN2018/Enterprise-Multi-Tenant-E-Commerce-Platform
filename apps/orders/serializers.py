"""Cart & order serializers."""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.orders.models import Cart, CartItem, Order, OrderItem


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="variant.product.name", read_only=True)
    sku = serializers.CharField(source="variant.sku", read_only=True)
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ("id", "variant", "product_name", "sku", "quantity", "unit_price", "line_total")
        read_only_fields = fields


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    item_count = serializers.SerializerMethodField()
    discount = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = (
            "id",
            "status",
            "items",
            "item_count",
            "coupon_code",
            "subtotal",
            "discount",
            "total",
            "updated_at",
        )
        read_only_fields = fields

    def get_item_count(self, obj) -> int:
        return sum(item.quantity for item in obj.items.all())

    def _discount_for(self, obj) -> Decimal:
        # Best-effort discount for display (coupon + automatic campaigns); the
        # authoritative figure is recomputed and re-validated at checkout.
        from apps.core import tenancy

        store = tenancy.get_current_store()
        if store is None:
            return Decimal("0.00")
        subtotal = obj.subtotal
        coupon_discount = Decimal("0.00")
        if obj.coupon_code:
            from apps.promotions.services import PromotionService

            service = PromotionService()
            coupon = service.find_active(store=store, code=obj.coupon_code)
            if coupon is not None and coupon.is_within_window():
                coupon_discount = service.compute_discount(coupon=coupon, subtotal=subtotal)
        from apps.promotions.engine import PromotionEngine

        auto = PromotionEngine().evaluate(store=store, items=obj.items.all(), subtotal=subtotal)
        return min(coupon_discount + auto.discount, subtotal)

    def get_discount(self, obj) -> str:
        return str(self._discount_for(obj))

    def get_total(self, obj) -> str:
        return str(max(obj.subtotal - self._discount_for(obj), Decimal("0.00")))


class AddCartItemSerializer(serializers.Serializer):
    variant_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=0)


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ("id", "variant", "product_name", "sku", "unit_price", "quantity", "line_total")
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "number",
            "status",
            "currency",
            "subtotal",
            "discount_total",
            "tax_total",
            "shipping_total",
            "total",
            "coupon_code",
            "shipping_method",
            "tracking_number",
            "placed_at",
            "items",
            "created_at",
        )
        read_only_fields = fields


class CheckoutSerializer(serializers.Serializer):
    shipping_method_id = serializers.UUIDField(required=False, allow_null=True)
    country = serializers.CharField(required=False, allow_blank=True, default="")
