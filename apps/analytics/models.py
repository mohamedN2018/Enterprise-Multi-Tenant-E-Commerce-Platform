"""Analytics domain model (store-scoped via ``TenantOwnedModel``).

``AnalyticsEvent`` is an append-only fact: a typed thing that happened in a store,
optionally attributed to a user, with a free-form ``data`` payload. Events are
recorded by :class:`apps.analytics.services.AnalyticsService` (usually from
domain-signal receivers) and rolled up by its ``summary``.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TenantOwnedModel


class AnalyticsEvent(TenantOwnedModel):
    event_type = models.CharField(max_length=64, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    data = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Analytics event"
        verbose_name_plural = "Analytics events"
        ordering = ("-occurred_at",)
        indexes = [
            models.Index(fields=["store", "event_type"]),
            models.Index(fields=["store", "occurred_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_type}@{self.store_id}"
