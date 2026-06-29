"""Admin registration for catalog models."""

from __future__ import annotations

from django.contrib import admin

from apps.catalog.models import Brand, BundleComponent, Category, Product, ProductVariant


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "store", "parent", "is_active", "position")
    list_filter = ("is_active",)
    search_fields = ("name", "slug", "store__name")


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "store", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "slug", "store__name")


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ("sku", "name", "price", "stock_quantity", "is_default", "is_active")


class BundleComponentInline(admin.TabularInline):
    model = BundleComponent
    fk_name = "bundle"
    extra = 0
    fields = ("component_variant", "quantity", "is_optional", "sort_order")
    autocomplete_fields = ("component_variant",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "store", "status", "product_type", "is_active", "created_at")
    list_filter = ("status", "product_type", "is_active")
    search_fields = ("name", "slug", "store__name")
    inlines = (ProductVariantInline, BundleComponentInline)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("sku", "product", "store", "price", "stock_quantity", "is_default", "is_active")
    list_filter = ("is_active", "is_default")
    search_fields = ("sku", "product__name", "store__name")
