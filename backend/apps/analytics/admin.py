"""Admin registration for analytics."""

from __future__ import annotations

from django.contrib import admin

from apps.analytics.models import AnalyticsEvent


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "store", "user", "occurred_at")
    list_filter = ("event_type",)
    search_fields = ("event_type", "store__name", "user__email")
    readonly_fields = ("occurred_at",)
