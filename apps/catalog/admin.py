"""Admin registration for catalog models."""

from __future__ import annotations

from django.contrib import admin

from apps.catalog.models import (
    Brand,
    BundleComponent,
    Category,
    DigitalAsset,
    DownloadGrant,
    LicenseKey,
    Product,
    ProductVariant,
)


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


@admin.register(DigitalAsset)
class DigitalAssetAdmin(admin.ModelAdmin):
    list_display = ("variant", "store", "requires_license", "download_limit", "is_active")
    list_filter = ("requires_license", "is_active")
    search_fields = ("variant__sku", "name", "store__name")


@admin.register(LicenseKey)
class LicenseKeyAdmin(admin.ModelAdmin):
    list_display = ("key", "variant", "store", "status", "assigned_user", "assigned_at")
    list_filter = ("status",)
    search_fields = ("key", "variant__sku", "store__name")


@admin.register(DownloadGrant)
class DownloadGrantAdmin(admin.ModelAdmin):
    list_display = (
        "token",
        "variant",
        "user",
        "order",
        "download_count",
        "download_limit",
        "expires_at",
    )
    search_fields = ("token", "variant__sku", "user__email", "order__number")
    readonly_fields = ("token", "download_count")
