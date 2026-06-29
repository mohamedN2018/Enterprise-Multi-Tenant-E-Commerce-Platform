"""Admin registration for promotions."""

from __future__ import annotations

from django.contrib import admin

from apps.promotions.models import Campaign, CampaignProduct, Coupon, CouponRedemption


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


class CampaignProductInline(admin.TabularInline):
    model = CampaignProduct
    extra = 0
    fields = ("product",)
    raw_id_fields = ("product",)


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "store",
        "campaign_type",
        "priority",
        "stackable",
        "is_active",
        "starts_at",
        "ends_at",
    )
    list_filter = ("campaign_type", "is_active", "stackable")
    search_fields = ("name", "description", "store__name")
    inlines = (CampaignProductInline,)


@admin.register(CampaignProduct)
class CampaignProductAdmin(admin.ModelAdmin):
    list_display = ("campaign", "product", "store", "created_at")
    search_fields = ("campaign__name", "product__name", "store__name")
