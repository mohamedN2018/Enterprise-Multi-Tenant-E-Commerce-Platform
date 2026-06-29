"""Notification domain models (store-scoped via ``TenantOwnedModel``).

* ``Notification``           — one in-app inbox entry for a recipient.
* ``NotificationPreference`` — a recipient's per-store channel opt-ins.

Notifications are produced by :class:`apps.notifications.services.NotificationService`
(typically from domain-signal receivers) and delivered over the channels the
recipient has enabled — always recorded in-app, optionally emailed.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.models import TenantOwnedModel


class NotificationChannel(models.TextChoices):
    IN_APP = "in_app", "In-app"
    EMAIL = "email", "Email"


class Notification(TenantOwnedModel):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    event_type = models.CharField(max_length=64, db_index=True)
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["recipient", "is_read"])]

    def __str__(self) -> str:
        return f"{self.event_type} -> {self.recipient_id}"


class NotificationPreference(TenantOwnedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_preferences"
    )
    in_app_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=False)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Notification preference"
        verbose_name_plural = "Notification preferences"
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["store", "user"],
                condition=Q(is_deleted=False),
                name="uniq_notification_pref_store_user",
            )
        ]

    def __str__(self) -> str:
        return f"prefs<{self.user_id}@{self.store_id}>"
