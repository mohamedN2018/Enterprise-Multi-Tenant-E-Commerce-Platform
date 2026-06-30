"""Admin registration for finance."""

from __future__ import annotations

from django.contrib import admin

from apps.finance.models import Currency, ExchangeRate, TaxRate, TaxZone


class TaxRateInline(admin.TabularInline):
    model = TaxRate
    extra = 0
    fields = ("name", "rate", "priority", "is_active")


@admin.register(TaxZone)
class TaxZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "store", "is_default")
    list_filter = ("is_default",)
    search_fields = ("name", "code", "store__name")
    inlines = (TaxRateInline,)


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "store", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name", "store__name")


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ("base_code", "target_code", "rate", "store")
    search_fields = ("base_code", "target_code", "store__name")
