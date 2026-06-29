"""Admin registration for promotions."""

from __future__ import annotations

from django.contrib import admin

from apps.promotions.models import Coupon, CouponRedemption


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "store",
        "discount_type",
        "value",
        "used_count",
        "usage_limit",
        "is_active",
    )
    list_filter = ("discount_type", "is_active")
    search_fields = ("code", "store__name")
    readonly_fields = ("used_count",)


@admin.register(CouponRedemption)
class CouponRedemptionAdmin(admin.ModelAdmin):
    list_display = ("coupon", "user", "order", "amount", "created_at")
    search_fields = ("coupon__code", "user__email", "order__number")
