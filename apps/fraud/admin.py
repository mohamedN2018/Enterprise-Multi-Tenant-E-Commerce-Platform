"""Admin registration for fraud."""

from __future__ import annotations

from django.contrib import admin

from apps.fraud.models import FraudCheck


@admin.register(FraudCheck)
class FraudCheckAdmin(admin.ModelAdmin):
    list_display = ("order", "store", "score", "decision", "resolution", "reviewed_at")
    list_filter = ("decision", "resolution")
    search_fields = ("order__number", "store__name")
    readonly_fields = ("score", "decision", "reasons", "reviewed_at")
