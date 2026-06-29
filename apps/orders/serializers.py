"""Cart & order serializers."""

from __future__ import annotations

from rest_framework import serializers

from apps.orders.models import Cart, CartItem, Order, OrderItem


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="variant.product.name", read_only=True)
    sku = serializers.CharField(source="variant.sku", read_only=True)
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = (
            "id",
            "variant",
            "product_name",
            "sku",
            "quantity",
            "unit_price",
            "line_total",
        )
        read_only_fields = fields


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ("id", "status", "items", "item_count", "subtotal", "updated_at")
        read_only_fields = fields

    def get_item_count(self, obj) -> int:
        return sum(item.quantity for item in obj.items.all())


class AddCartItemSerializer(serializers.Serializer):
    variant_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=0)


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = (
            "id",
            "variant",
            "product_name",
            "sku",
            "unit_price",
            "quantity",
            "line_total",
        )
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
            "tax_total",
            "total",
            "placed_at",
            "items",
            "created_at",
        )
        read_only_fields = fields
