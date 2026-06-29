"""Admin registration for rewards."""

from __future__ import annotations

from django.contrib import admin

from apps.rewards.models import (
    GiftCard,
    LoyaltyAccount,
    LoyaltyTransaction,
    Wallet,
    WalletTransaction,
)


class WalletTransactionInline(admin.TabularInline):
    model = WalletTransaction
    extra = 0
    readonly_fields = ("txn_type", "amount", "balance_after", "reason", "reference", "created_at")
    can_delete = False


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("user", "store", "balance", "currency")
    search_fields = ("user__email", "store__name")
    readonly_fields = ("balance",)
    inlines = (WalletTransactionInline,)


@admin.register(GiftCard)
class GiftCardAdmin(admin.ModelAdmin):
    list_display = ("code", "store", "initial_balance", "balance", "status")
    list_filter = ("status",)
    search_fields = ("code", "store__name")


class LoyaltyTransactionInline(admin.TabularInline):
    model = LoyaltyTransaction
    extra = 0
    readonly_fields = ("txn_type", "points", "balance_after", "reason", "reference", "created_at")
    can_delete = False


@admin.register(LoyaltyAccount)
class LoyaltyAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "store", "points")
    search_fields = ("user__email", "store__name")
    inlines = (LoyaltyTransactionInline,)
