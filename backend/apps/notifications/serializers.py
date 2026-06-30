"""Notification serializers."""

from __future__ import annotations

from rest_framework import serializers

from apps.notifications.models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = (
            "id",
            "event_type",
            "title",
            "body",
            "data",
            "is_read",
            "read_at",
            "created_at",
        )
        read_only_fields = fields


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = ("in_app_enabled", "email_enabled", "updated_at")
        read_only_fields = ("updated_at",)
