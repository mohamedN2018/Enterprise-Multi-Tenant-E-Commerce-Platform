"""Admin registration for returns."""

from __future__ import annotations

from django.contrib import admin

from apps.returns.models import ReturnItem, ReturnRequest


class ReturnItemInline(admin.TabularInline):
    model = ReturnItem
    extra = 0
    fields = ("order_item", "variant", "quantity", "reason")
    autocomplete_fields = ("variant",)


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "user", "store", "status", "resolution", "refund_amount")
    list_filter = ("status", "resolution")
    search_fields = ("order__number", "user__email", "store__name")
    readonly_fields = ("refund_amount", "refund_reference", "processed_at")
    inlines = (ReturnItemInline,)
