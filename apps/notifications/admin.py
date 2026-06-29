"""Admin registration for notifications."""

from __future__ import annotations

from django.contrib import admin

from apps.notifications.models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("event_type", "recipient", "store", "title", "is_read", "created_at")
    list_filter = ("is_read", "event_type")
    search_fields = ("title", "recipient__email", "store__name")
    readonly_fields = ("read_at",)


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "store", "in_app_enabled", "email_enabled")
    list_filter = ("in_app_enabled", "email_enabled")
    search_fields = ("user__email", "store__name")
