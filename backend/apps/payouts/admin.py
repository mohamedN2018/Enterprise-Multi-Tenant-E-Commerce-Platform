"""Admin registration for payouts."""

from __future__ import annotations

from django.contrib import admin

from apps.payouts.models import LedgerEntry, Payout, SellerAccount


class LedgerEntryInline(admin.TabularInline):
    model = LedgerEntry
    extra = 0
    can_delete = False
    readonly_fields = (
        "entry_type",
        "order",
        "gross_amount",
        "commission_amount",
        "net_amount",
        "balance_after",
        "reference",
        "created_at",
    )


@admin.register(SellerAccount)
class SellerAccountAdmin(admin.ModelAdmin):
    list_display = ("store", "balance", "currency", "commission_rate")
    search_fields = ("store__name",)
    readonly_fields = ("balance",)
    inlines = (LedgerEntryInline,)


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ("store", "amount", "status", "paid_at", "created_at")
    list_filter = ("status",)
    search_fields = ("store__name", "reference")
