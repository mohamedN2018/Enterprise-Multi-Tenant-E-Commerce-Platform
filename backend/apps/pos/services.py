"""Cashier (POS) integration service.

Owns the write side of the cashier link: issuing/rotating the API key, wiring the
outbound webhook, and — the core of it — deducting warehouse stock when the
cashier reports an in-store sale so the shared inventory stays correct.
"""

from __future__ import annotations

import logging
import urllib.error
import urllib.request
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Q
from django.utils import timezone

from apps.catalog.models import Category, Product, ProductStatus, ProductVariant
from apps.catalog.repositories import ProductVariantRepository
from apps.catalog.services import CatalogService
from apps.core.exceptions import ConflictError, NotFoundError, ValidationError
from apps.core.services import BaseService, atomic
from apps.inventory.models import StockItem
from apps.inventory.services import InventoryService
from apps.pos import keys
from apps.pos.client import PosSupplierClient
from apps.pos.models import PosConnection, PosImportedProduct, PosSupplierConnection

logger = logging.getLogger(__name__)


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


class PosSupplierService(BaseService):
    """Outbound link: verify the external POS and import its catalog.

    Import is idempotent — each external product is matched (by prior import, then
    barcode) and upserted, so re-running only updates. Prices/stock land on the
    product's default variant; stock flows into the warehouse via the catalog
    service's stock sync, so imported items are immediately sellable.
    """

    def __init__(self):
        self.catalog = CatalogService()

    @staticmethod
    def store_public_url(store) -> str:
        return f"{settings.FRONTEND_URL.rstrip('/')}/store/{store.slug}"

    def _client(self, *, store, api_url: str, api_key: str) -> PosSupplierClient:
        return PosSupplierClient(
            api_url=api_url,
            api_key=api_key,
            store_name=store.name,
            store_url=self.store_public_url(store),
        )

    # --- Connection lifecycle ---
    @atomic
    def connect(self, *, store, provider: str, api_url: str, api_key: str) -> PosSupplierConnection:
        # Prove the key works before persisting anything (raises on 401 / unreachable).
        summary = self._client(store=store, api_url=api_url, api_key=api_key).verify()

        connection = PosSupplierConnection.all_objects.filter(store=store, is_deleted=False).first()
        if connection is None:
            connection = PosSupplierConnection(store=store)
        connection.provider = provider or "q-shop POS"
        connection.api_url = api_url
        connection.api_key = api_key
        connection.is_connected = True
        connection.remote_store_name = str(summary.get("store") or "")
        connection.remote_product_count = int(summary.get("productCount") or 0)
        connection.last_verified_at = timezone.now()
        connection.save()
        return connection

    @atomic
    def disconnect(self, *, connection: PosSupplierConnection) -> None:
        connection.delete()

    # --- Import ---
    @atomic
    def import_products(self, *, connection: PosSupplierConnection) -> dict:
        store = connection.store
        products = self._client(
            store=store, api_url=connection.api_url, api_key=connection.api_key
        ).fetch_products()

        created = updated = skipped = 0
        for item in products:
            if not item or not item.get("id") or not item.get("name"):
                skipped += 1
                continue
            was_new = self._upsert(store=store, connection=connection, item=item)
            created += int(was_new)
            updated += int(not was_new)

        connection.last_synced_at = timezone.now()
        connection.last_import_created = created
        connection.last_import_updated = updated
        connection.remote_product_count = created + updated
        connection.save(
            update_fields=[
                "last_synced_at",
                "last_import_created",
                "last_import_updated",
                "remote_product_count",
                "updated_at",
            ]
        )
        return {"created": created, "updated": updated, "skipped": skipped}

    # --- Upsert one external product ---
    def _upsert(self, *, store, connection: PosSupplierConnection, item: dict) -> bool:
        external_id = str(item["id"])
        barcode = str(item.get("barcode") or "").strip()
        price = self._decimal(item.get("price"))
        cost = self._decimal(item.get("cost"), allow_none=True)
        stock = max(int(item.get("stock") or 0), 0)
        published = item.get("is_active", True)
        category = self._category(store=store, name=item.get("category"))

        product, ref = self._match(store=store, connection=connection, external_id=external_id, barcode=barcode)
        product_data = {
            "name": item["name"],
            "name_en": item.get("name_en") or "",
            "description": item.get("description") or "",
            "category": category,
            "status": ProductStatus.PUBLISHED if published else ProductStatus.DRAFT,
        }
        is_new = product is None
        if is_new:
            product = self.catalog.create_product(store=store, data=product_data)
        else:
            self.catalog.update_product(instance=product, data=product_data)

        variant_data = {
            "barcode": barcode,
            "price": price,
            "cost_price": cost,
            "stock_quantity": stock,
        }
        variant = ProductVariant.all_objects.filter(
            store=store, product=product, is_default=True, is_deleted=False
        ).first()
        if variant is None:
            variant_data["sku"] = self._free_sku(store=store, candidates=[item.get("sku"), barcode, external_id])
            variant_data["is_default"] = True
            self.catalog.create_variant(store=store, product=product, data=variant_data)
        else:
            self.catalog.update_variant(instance=variant, data=variant_data)

        if is_new and item.get("image_url"):
            self._maybe_set_image(product, item["image_url"])

        if ref is None:
            PosImportedProduct.objects.create(
                store=store,
                connection=connection,
                external_id=external_id,
                barcode=barcode,
                product=product,
            )
        elif ref.barcode != barcode:
            ref.barcode = barcode
            ref.save(update_fields=["barcode", "updated_at"])
        return is_new

    def _match(self, *, store, connection, external_id, barcode):
        """Return (product, ref) for an external item, or (None, None) if new."""
        ref = PosImportedProduct.all_objects.filter(
            store=store, connection=connection, external_id=external_id, is_deleted=False
        ).first()
        if ref is not None:
            return ref.product, ref
        if barcode:
            variant = ProductVariant.all_objects.filter(
                store=store, barcode=barcode, is_deleted=False
            ).first()
            if variant is not None:
                return variant.product, None
        return None, None

    def _category(self, *, store, name):
        name = (name or "").strip()
        if not name:
            return None
        existing = (
            Category.all_objects.filter(store=store, is_deleted=False)
            .filter(Q(name=name) | Q(name_en=name))
            .first()
        )
        if existing is not None:
            return existing
        return self.catalog.create_category(store=store, data={"name": name})

    @staticmethod
    def _free_sku(*, store, candidates: list) -> str:
        repo = ProductVariantRepository()
        seen = [str(c).strip() for c in candidates if c and str(c).strip()]
        for candidate in seen:
            if not repo.sku_exists(store=store, sku=candidate):
                return candidate
        base = seen[0] if seen else "SKU"
        for i in range(2, 100):
            candidate = f"{base}-{i}"
            if not repo.sku_exists(store=store, sku=candidate):
                return candidate
        return f"{base}-{timezone.now().timestamp():.0f}"

    @staticmethod
    def _decimal(value, *, allow_none: bool = False):
        if value is None or value == "":
            return None if allow_none else Decimal("0")
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError):
            return None if allow_none else Decimal("0")

    @staticmethod
    def _maybe_set_image(product: Product, image_url: str) -> None:
        try:
            request = urllib.request.Request(image_url, headers={"User-Agent": "qshop-import"})
            with urllib.request.urlopen(request, timeout=8) as resp:
                if getattr(resp, "status", 200) != 200:
                    return
                data = resp.read(5 * 1024 * 1024)  # cap at 5 MB
            if not data:
                return
            ext = (image_url.rsplit(".", 1)[-1].split("?")[0] or "jpg")[:5]
            product.image.save(f"pos-{product.id}.{ext}", ContentFile(data), save=True)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            logger.warning("POS image import failed for %s: %s", image_url, exc)
