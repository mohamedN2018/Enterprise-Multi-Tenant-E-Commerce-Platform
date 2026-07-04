"""Lean, public-facing serializers for the storefront.

Deliberately expose only what a shopper needs — no cost prices, internal flags,
or staff metadata.
"""

from __future__ import annotations

from django.db.models import Sum
from rest_framework import serializers

from apps.catalog.models import Category, Product, ProductVariant
from apps.core.i18n import localized
from apps.inventory.models import StockItem
from apps.reviews.models import Review
from apps.stores.models import Store


class LocalizedNameMixin:
    """Serve ``name``/``description`` in the request's language (Arabic default)."""

    def get_name(self, obj):
        return localized(obj, "name", self.context)

    def get_description(self, obj):
        return localized(obj, "description", self.context)


class StorefrontReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = (
            "id",
            "rating",
            "title",
            "body",
            "is_verified_purchase",
            "helpful_count",
            "created_at",
        )
        read_only_fields = fields


class StorefrontStoreSerializer(LocalizedNameMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = Store
        fields = ("id", "name", "slug", "description", "logo", "banner", "currency", "country")
        read_only_fields = fields


class StorefrontCategorySerializer(LocalizedNameMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    product_count = serializers.IntegerField(read_only=True)
    store_slug = serializers.CharField(source="store.slug", read_only=True)

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description", "product_count", "store", "store_slug")
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


class StorefrontProductSerializer(LocalizedNameMixin, serializers.ModelSerializer):
    """List representation: the product plus its cheapest sellable price."""

    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    compare_at_price = serializers.SerializerMethodField()
    currency = serializers.CharField(source="store.currency", read_only=True)
    store = serializers.UUIDField(source="store_id", read_only=True)
    store_slug = serializers.CharField(source="store.slug", read_only=True)
    rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "product_type",
            "price",
            "compare_at_price",
            "currency",
            "store",
            "store_slug",
            "rating",
            "review_count",
        )
        read_only_fields = fields

    def get_compare_at_price(self, obj):
        variant = self._default_variant(obj)
        cap = getattr(variant, "compare_at_price", None) if variant else None
        # Only a genuine discount (was-price above the current price).
        if cap and variant and cap > variant.price:
            return str(cap)
        return None

    def get_rating(self, obj):
        # Populated by the view's annotation; defaults to 0 when not annotated.
        return round(float(getattr(obj, "rating_avg", None) or 0), 1)

    def get_review_count(self, obj):
        return int(getattr(obj, "rating_count", 0) or 0)

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
