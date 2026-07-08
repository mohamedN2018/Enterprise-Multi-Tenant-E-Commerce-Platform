"""Lean, public-facing serializers for the storefront.

Deliberately expose only what a shopper needs — no cost prices, internal flags,
or staff metadata.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.catalog.models import Category, Product, ProductVariant
from apps.core.i18n import localized
from apps.reviews.models import Review
from apps.stores.models import Store


def variant_available(variant) -> bool:
    """Whether a single variant is sellable, from *prefetched* stock items.

    Untracked variants (e.g. digital) are always available; tracked ones need net
    warehouse stock (on-hand minus reserved) in at least one warehouse. Relies on
    the view having prefetched ``variants__stock_items`` (via ``all_objects``), so
    it adds no per-variant query.
    """
    if not variant.track_inventory:
        return True
    return any(
        (item.quantity - item.reserved_quantity) > 0
        for item in variant.stock_items.all()
        if not item.is_deleted
    )


def variant_available_qty(variant):
    """Net sellable units for a tracked variant (on-hand minus reserved), or None
    for an untracked variant (treated as unlimited). Lets the storefront cap the
    order quantity to what's actually in stock. Uses prefetched stock items."""
    if not variant.track_inventory:
        return None
    return sum(
        max(item.quantity - item.reserved_quantity, 0)
        for item in variant.stock_items.all()
        if not item.is_deleted
    )


def product_in_stock(product) -> bool:
    """A product is in stock if any of its active variants is available."""
    return any(variant_available(v) for v in product.variants.all() if v.is_active)


class LocalizedNameMixin:
    """Serve ``name``/``description`` in the request's language (Arabic default)."""

    def get_name(self, obj):
        return localized(obj, "name", self.context)

    def get_description(self, obj):
        return localized(obj, "description", self.context)


def image_url(obj):
    """Origin-relative media URL (e.g. ``/media/products/x.png``).

    We serve the SPA and its API from a single origin (nginx proxies ``/media``),
    so a relative URL resolves correctly on any host/port/scheme — unlike an
    absolute URL built from the request's ``Host`` header.
    """
    return obj.image.url if obj.image else None


def gallery_items(product) -> list[dict]:
    """Ordered gallery as ``{image, alt}`` objects; empty if the product has none."""
    return [
        {"image": img.image.url, "alt": img.alt_text or ""}
        for img in product.images.all()
        if img.image
    ]


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
    available = serializers.SerializerMethodField()

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
            "available",
        )
        read_only_fields = fields

    def get_in_stock(self, obj) -> bool:
        return variant_available(obj)

    def get_available(self, obj):
        return variant_available_qty(obj)


class StorefrontProductSerializer(LocalizedNameMixin, serializers.ModelSerializer):
    """List representation: the product plus its cheapest sellable price."""

    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    compare_at_price = serializers.SerializerMethodField()
    currency = serializers.CharField(source="store.currency", read_only=True)
    store = serializers.UUIDField(source="store_id", read_only=True)
    store_slug = serializers.CharField(source="store.slug", read_only=True)
    rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "image",
            "images",
            "product_type",
            "price",
            "compare_at_price",
            "currency",
            "store",
            "store_slug",
            "rating",
            "review_count",
            "in_stock",
        )
        read_only_fields = fields

    def get_in_stock(self, obj) -> bool:
        return product_in_stock(obj)

    def get_image(self, obj):
        # Primary/cover URL: first gallery image, else the legacy single image.
        gallery = gallery_items(obj)
        return gallery[0]["image"] if gallery else image_url(obj)

    def get_images(self, obj):
        # Full gallery as {image, alt} objects; fall back to the legacy single
        # image so older products still return a one-item list.
        gallery = gallery_items(obj)
        if gallery:
            return gallery
        legacy = image_url(obj)
        return [{"image": legacy, "alt": ""}] if legacy else []

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
