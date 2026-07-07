"""Cashier (POS) integration service.

Owns the write side of the cashier link: issuing/rotating the API key, wiring the
outbound webhook, and — the core of it — deducting warehouse stock when the
cashier reports an in-store sale so the shared inventory stays correct.
"""

from __future__ import annotations

from django.utils import timezone

from apps.catalog.models import ProductVariant
from apps.core.exceptions import ConflictError, NotFoundError, ValidationError
from apps.core.services import BaseService, atomic
from apps.inventory.models import StockItem
from apps.inventory.services import InventoryService
from apps.pos import keys
from apps.pos.models import PosConnection


class PosService(BaseService):
    # --- Connection lifecycle ---
    @atomic
    def create_connection(self, *, store, name: str = "Cashier", webhook_url: str = "") -> tuple:
        if PosConnection.all_objects.filter(store=store, is_deleted=False).exists():
            raise ConflictError(
                "This store is already linked to a cashier system.", code="pos_already_linked"
            )
        plain = keys.generate_key()
        connection = PosConnection.objects.create(
            store=store,
            name=name or "Cashier",
            api_key_prefix=keys.key_prefix(plain),
            api_key_hash=keys.hash_key(plain),
            webhook_url=webhook_url or "",
            webhook_secret=keys.generate_key() if webhook_url else "",
        )
        return connection, plain

    @atomic
    def rotate_key(self, *, connection: PosConnection) -> str:
        """Issue a fresh key, invalidating the old one. Returns the plaintext once."""
        plain = keys.generate_key()
        connection.api_key_prefix = keys.key_prefix(plain)
        connection.api_key_hash = keys.hash_key(plain)
        connection.save(update_fields=["api_key_prefix", "api_key_hash", "updated_at"])
        return plain

    @atomic
    def update_connection(self, *, connection: PosConnection, data: dict) -> PosConnection:
        if "name" in data:
            connection.name = data["name"] or "Cashier"
        if "is_active" in data:
            connection.is_active = bool(data["is_active"])
        if "webhook_url" in data:
            connection.webhook_url = data["webhook_url"] or ""
            # A URL needs a signing secret; clearing the URL clears the secret.
            if connection.webhook_url and not connection.webhook_secret:
                connection.webhook_secret = keys.generate_key()
            if not connection.webhook_url:
                connection.webhook_secret = ""
        connection.save()
        return connection

    def touch(self, *, connection: PosConnection) -> None:
        connection.last_used_at = timezone.now()
        connection.save(update_fields=["last_used_at", "updated_at"])

    # --- Inbound: the cashier sells, the warehouse deducts ---
    @atomic
    def record_sale(self, *, connection: PosConnection, items: list[dict], reference: str = "") -> list[dict]:
        """Deduct each sold line from the store's default warehouse and ledger it.

        ``items`` is ``[{"sku": str, "quantity": int}, ...]``. The whole sale is
        atomic: an unknown SKU or a short line rolls the entire sale back, so the
        cashier never half-applies. Returns the resulting stock snapshot per SKU.
        """
        if not items:
            raise ValidationError("A sale must contain at least one line item.")
        store = connection.store
        warehouse = InventoryService.default_warehouse(store=store)
        inventory = InventoryService()
        ref = f"pos-sale:{connection.id}:{reference}".rstrip(":")

        results = []
        for line in items:
            variant = self._variant(store=store, sku=line["sku"])
            inventory.issue(
                store=store,
                variant=variant,
                warehouse=warehouse,
                quantity=int(line["quantity"]),
                reference=ref,
                note="POS in-store sale",
            )
            results.append(self._variant_stock(store=store, variant=variant))
        self.touch(connection=connection)
        return results

    # --- Outbound / pull: current levels ---
    def stock_snapshot(self, *, store, skus: list[str] | None = None) -> list[dict]:
        variants = ProductVariant.all_objects.filter(store=store, is_deleted=False, is_active=True)
        if skus:
            variants = variants.filter(sku__in=skus)
        return [self._variant_stock(store=store, variant=v) for v in variants]

    # --- Helpers ---
    @staticmethod
    def _variant(*, store, sku: str) -> ProductVariant:
        variant = ProductVariant.all_objects.filter(
            store=store, sku=sku, is_deleted=False
        ).first()
        if variant is None:
            raise NotFoundError(
                f"No product variant with SKU '{sku}' in this store.", code="unknown_sku"
            )
        return variant

    @staticmethod
    def _variant_stock(*, store, variant: ProductVariant) -> dict:
        items = StockItem.all_objects.filter(store=store, variant=variant, is_deleted=False)
        on_hand = sum(i.quantity for i in items)
        reserved = sum(i.reserved_quantity for i in items)
        available = max(on_hand - reserved, 0)
        tracked = variant.track_inventory
        return {
            "sku": variant.sku,
            "name": variant.name,
            "on_hand": on_hand,
            "reserved": reserved,
            "available": available,
            "in_stock": True if not tracked else available > 0,
        }
