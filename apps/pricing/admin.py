"""Admin registration for pricing."""

from __future__ import annotations

from django.contrib import admin

from apps.pricing.models import CustomerGroup, CustomerGroupMembership, PriceRule


@admin.register(CustomerGroup)
class CustomerGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "store", "is_default", "priority")
    list_filter = ("is_default",)
    search_fields = ("name", "code", "store__name")


@admin.register(CustomerGroupMembership)
class CustomerGroupMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "customer_group", "store", "created_at")
    search_fields = ("user__email", "customer_group__name")


@admin.register(PriceRule)
class PriceRuleAdmin(admin.ModelAdmin):
    list_display = ("variant", "customer_group", "min_quantity", "rule_type", "value", "is_active")
    list_filter = ("rule_type", "is_active")
    search_fields = ("variant__sku",)
