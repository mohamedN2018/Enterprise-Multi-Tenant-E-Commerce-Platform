"""Catalog serializers.

Related fields (``parent``/``category``/``brand``) resolve their querysets from
the tenant-scoped default manager, so a payload can only reference objects that
belong to the active store — cross-store references are rejected automatically.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.catalog.models import Brand, BundleComponent, Category, Product, ProductVariant


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
            "parent",
            "description",
            "is_active",
            "position",
            "meta_title",
            "meta_description",
            "meta_keywords",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at")


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "meta_title",
            "meta_description",
            "meta_keywords",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at")


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "product",
            "name",
            "sku",
            "barcode",
            "price",
            "compare_at_price",
            "cost_price",
            "stock_quantity",
            "track_inventory",
            "weight",
            "options",
            "is_default",
            "position",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "product", "created_at", "updated_at")


class BundleComponentSerializer(serializers.ModelSerializer):
    component_sku = serializers.CharField(source="component_variant.sku", read_only=True)

    class Meta:
        model = BundleComponent
        fields = (
            "id",
            "component_variant",
            "component_sku",
            "quantity",
            "is_optional",
            "sort_order",
        )
        read_only_fields = fields


class BundleComponentCreateSerializer(serializers.Serializer):
    component_variant_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    is_optional = serializers.BooleanField(default=False)
    sort_order = serializers.IntegerField(min_value=0, default=0)


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    components = BundleComponentSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "category",
            "brand",
            "product_type",
            "kind",
            "status",
            "is_active",
            "published_at",
            "meta_title",
            "meta_description",
            "meta_keywords",
            "variants",
            "components",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "slug",
            "published_at",
            "variants",
            "components",
            "created_at",
            "updated_at",
        )
