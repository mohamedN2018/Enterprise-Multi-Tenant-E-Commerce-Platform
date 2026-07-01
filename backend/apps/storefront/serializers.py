"""Lean, public-facing serializers for the storefront.

Deliberately expose only what a shopper needs — no cost prices, internal flags,
or staff metadata.
"""

from __future__ import annotations

from django.db.models import Sum
from rest_framework import serializers

from apps.catalog.models import Product, ProductVariant
from apps.inventory.models import StockItem
from apps.stores.models import Store


class StorefrontStoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ("id", "name", "slug", "description", "logo", "banner", "currency", "country")
        read_only_fields = fields


class StorefrontVariantSerializer(serializers.ModelSerializer):
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "name",
            "sku",
            "price",
            "compare_at_price",
            "is_default",
            "in_stock",
        )
        read_only_fields = fields

    def get_in_stock(self, obj) -> bool:
        # Untracked variants (e.g. digital) are always available; otherwise use
        # real warehouse availability (on-hand minus reserved across warehouses).
        if not obj.track_inventory:
            return True
        agg = StockItem.all_objects.filter(variant=obj, is_deleted=False).aggregate(
            on_hand=Sum("quantity"), reserved=Sum("reserved_quantity")
        )
        return max((agg["on_hand"] or 0) - (agg["reserved"] or 0), 0) > 0


class StorefrontProductSerializer(serializers.ModelSerializer):
    """List representation: the product plus its cheapest sellable price."""

    price = serializers.SerializerMethodField()
    currency = serializers.CharField(source="store.currency", read_only=True)
    store = serializers.UUIDField(source="store_id", read_only=True)
    store_slug = serializers.CharField(source="store.slug", read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "product_type",
            "price",
            "currency",
            "store",
            "store_slug",
        )
        read_only_fields = fields

    @staticmethod
    def _default_variant(obj):
        variants = [v for v in obj.variants.all() if v.is_active]
        if not variants:
            return None
        return next((v for v in variants if v.is_default), variants[0])

    def get_price(self, obj):
        variant = self._default_variant(obj)
        return str(variant.price) if variant else None


class StorefrontProductDetailSerializer(StorefrontProductSerializer):
    """Detail representation: adds the purchasable variants."""

    variants = serializers.SerializerMethodField()

    class Meta(StorefrontProductSerializer.Meta):
        fields = (*StorefrontProductSerializer.Meta.fields, "variants")

    def get_variants(self, obj):
        variants = [v for v in obj.variants.all() if v.is_active]
        return StorefrontVariantSerializer(variants, many=True).data
