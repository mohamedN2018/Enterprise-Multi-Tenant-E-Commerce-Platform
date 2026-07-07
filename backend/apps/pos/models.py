"""Cashier (POS) integration models.

Two complementary links, each optional and one-per-store:

* :class:`PosConnection` — *inbound*. A cashier presents an API key (stored
  hashed) to report in-store sales and read stock; an optional webhook pushes
  online stock changes back to it.
* :class:`PosSupplierConnection` — *outbound*. The store pulls its catalog **from**
  an external POS (e.g. "q-shop POS") using that POS's API URL + key. Products are
  upserted and tracked by :class:`PosImportedProduct` for idempotent re-imports.
"""

from __future__ import annotations

from django.db import models
from django.db.models import Q

from apps.core.models import TenantOwnedModel
from apps.pos.fields import EncryptedTextField


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


class PosSupplierConnection(TenantOwnedModel):
    """The store's outbound link to an external POS it imports products from."""

    provider = models.CharField(max_length=80, default="q-shop POS")
    api_url = models.URLField()
    # The supplier's key that WE present. Encrypted at rest; never returned by the
    # API (write-only).
    api_key = EncryptedTextField()
    is_connected = models.BooleanField(default=False, db_index=True)
    # Snapshot from the last successful verify.
    remote_store_name = models.CharField(max_length=255, blank=True)
    remote_product_count = models.PositiveIntegerField(default=0)
    last_verified_at = models.DateTimeField(null=True, blank=True)
    # Last import summary.
    last_synced_at = models.DateTimeField(null=True, blank=True)
    last_import_created = models.PositiveIntegerField(default=0)
    last_import_updated = models.PositiveIntegerField(default=0)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "POS supplier connection"
        constraints = [
            models.UniqueConstraint(
                fields=["store"],
                condition=Q(is_deleted=False),
                name="uniq_pos_supplier_per_store",
            )
        ]

    def __str__(self) -> str:
        return f"{self.provider} → {self.store_id}"


class PosImportedProduct(TenantOwnedModel):
    """Maps an external POS product id to the local product, for idempotent sync."""

    connection = models.ForeignKey(
        PosSupplierConnection, on_delete=models.CASCADE, related_name="imported"
    )
    external_id = models.CharField(max_length=128, db_index=True)
    barcode = models.CharField(max_length=64, blank=True, db_index=True)
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.CASCADE, related_name="pos_imports"
    )

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "POS imported product"
        constraints = [
            models.UniqueConstraint(
                fields=["connection", "external_id"],
                condition=Q(is_deleted=False),
                name="uniq_pos_import_external_id",
            )
        ]
