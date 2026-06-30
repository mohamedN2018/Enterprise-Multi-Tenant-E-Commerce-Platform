"""Wishlist serializers."""

from __future__ import annotations

from rest_framework import serializers

from apps.wishlist.models import WishlistItem


class WishlistItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="variant.product.name", read_only=True)
    sku = serializers.CharField(source="variant.sku", read_only=True)
    unit_price = serializers.DecimalField(
        source="variant.price", max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = WishlistItem
        fields = ("id", "variant", "product_name", "sku", "unit_price", "created_at")
        read_only_fields = fields


class AddWishlistItemSerializer(serializers.Serializer):
    variant_id = serializers.UUIDField()


class MoveToCartSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, required=False, default=1)
