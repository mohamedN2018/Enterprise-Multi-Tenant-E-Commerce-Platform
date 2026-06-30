"""Admin registration for shipping."""

from __future__ import annotations

from django.contrib import admin

from apps.shipping.models import ShippingMethod, ShippingZone


class ShippingMethodInline(admin.TabularInline):
    model = ShippingMethod
    extra = 0
    fields = ("name", "price", "per_kg", "free_over", "is_active")


@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "store", "is_default")
    list_filter = ("is_default",)
    search_fields = ("name", "code", "store__name")
    inlines = (ShippingMethodInline,)


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ("name", "zone", "store", "price", "per_kg", "free_over", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "zone__name", "store__name")
