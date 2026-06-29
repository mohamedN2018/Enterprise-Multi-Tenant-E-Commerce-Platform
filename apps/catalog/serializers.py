"""Catalog serializers.

Related fields (``parent``/``category``/``brand``) resolve their querysets from
the tenant-scoped default manager, so a payload can only reference objects that
belong to the active store — cross-store references are rejected automatically.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.catalog.models import Brand, Category, Product, ProductVariant


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


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)

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
            "status",
            "is_active",
            "published_at",
            "meta_title",
            "meta_description",
            "meta_keywords",
            "variants",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "slug",
            "published_at",
            "variants",
            "created_at",
            "updated_at",
        )
