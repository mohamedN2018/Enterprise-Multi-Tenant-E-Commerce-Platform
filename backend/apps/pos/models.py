"""Cashier (POS) integration models.

A store links one external cashier system via a :class:`PosConnection`:
  * ``api_key_*``      — the inbound credential the cashier presents to report
    in-store sales and read stock levels (stored hashed; see ``keys``).
  * ``webhook_url``    — the outbound target the platform POSTs to when online
    stock changes, so the cashier stays in sync (two-way).
"""

from __future__ import annotations

from django.db import models
from django.db.models import Q

from apps.core.models import TenantOwnedModel


class PosConnection(TenantOwnedModel):
    name = models.CharField(max_length=120, default="Cashier")
    # Inbound credential (cashier -> platform). Only the hash is persisted.
    api_key_prefix = models.CharField(max_length=16, db_index=True)
    api_key_hash = models.CharField(max_length=64, db_index=True)
    # Outbound sync (platform -> cashier). Optional; blank disables the push.
    webhook_url = models.URLField(blank=True)
    webhook_secret = models.CharField(max_length=64, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "POS connection"
        constraints = [
            # One live cashier link per store.
            models.UniqueConstraint(
                fields=["store"],
                condition=Q(is_deleted=False),
                name="uniq_pos_connection_per_store",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.api_key_prefix}…)"
