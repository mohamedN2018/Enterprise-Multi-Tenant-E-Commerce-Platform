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
from django.db import transaction
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
from apps.pos.client import PosAuthError, PosSupplierClient, PosUnavailableError
from apps.pos.models import PosConnection, PosImportedProduct, PosSupplierConnection
from apps.pos.security import assert_public_url, is_public_url, open_public_url

logger = logging.getLogger(__name__)


class PosService(BaseService):
    # --- Connection lifecycle ---
    @atomic
    def create_connection(self, *, store, name: str = "Cashier", webhook_url: str = "") -> tuple:
        if PosConnection.all_objects.filter(store=store, is_deleted=False).exists():
            raise ConflictError(
                "This store is already linked to a cashier system.", code="pos_already_linked"
            )
        # The webhook is fetched server-side (push_stock_update) — block SSRF targets.
        if webhook_url:
            assert_public_url(webhook_url)
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
            if data["webhook_url"]:
                assert_public_url(data["webhook_url"])  # block SSRF targets
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

    # --- Inbound: the cashier reports a status change for an online order ---
    # Cashier vocabulary -> our fulfillment status (two-way sync).
    _ORDER_STATUS_MAP = {
        "accepted": "processing",
        "preparing": "processing",
        "processing": "processing",
        "ready": "shipped",
        "shipped": "shipped",
        "out_for_delivery": "out_for_delivery",
        "on_the_way": "out_for_delivery",
        "shipping": "out_for_delivery",
        "delivered": "delivered",
        "completed": "delivered",
        "fulfilled": "delivered",
        "cancelled": "cancelled",
        "canceled": "cancelled",
        "rejected": "cancelled",
    }

    def record_order_status(self, *, connection: PosConnection, external_id: str, status: str, note: str = ""):
        """Map a cashier status onto the matching store order (by its number) and
        apply it. Unknown statuses are accepted but ignored so the cashier is never
        blocked. Returns the order."""
        from apps.orders.models import Order
        from apps.orders.services import CheckoutService

        order = Order.all_objects.filter(
            store=connection.store, number=external_id, is_deleted=False
        ).first()
        if order is None:
            raise NotFoundError(
                "No order with this reference in this store.", code="order_not_found"
            )
        mapped = self._ORDER_STATUS_MAP.get(str(status or "").strip().lower())
        self.touch(connection=connection)
        if mapped is None:
            return order  # unrecognised status — no-op, don't block the cashier
        return CheckoutService().apply_pos_status(
            order=order, status=mapped, note=note or f"cashier: {status}"
        )

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
        # Block SSRF: never let a seller point us at a private/internal address.
        assert_public_url(api_url)
        # Prove the key works before persisting anything (raises on 401 / unreachable).
        summary = self._client(store=store, api_url=api_url, api_key=api_key).verify()

        connection = PosSupplierConnection.all_objects.filter(store=store, is_deleted=False).first()
        if connection is None:
            connection = PosSupplierConnection(store=store)
        connection.provider = provider or "q-shop POS"
        connection.api_url = api_url
        connection.api_key = api_key
        connection.is_connected = True
        connection.remote_store_name = str(summary.get("store") or "")[:255]
        connection.remote_product_count = self._safe_int(summary.get("productCount"))
        connection.last_verified_at = timezone.now()
        connection.save()
        return connection

    @atomic
    def disconnect(self, *, connection: PosSupplierConnection) -> None:
        connection.delete()

    # --- Import ---
    def import_products(self, *, connection: PosSupplierConnection) -> dict:
        store = connection.store
        products = self._client(
            store=store, api_url=connection.api_url, api_key=connection.api_key
        ).fetch_products()

        created = updated = skipped = 0
        for item in products:
            if not isinstance(item, dict) or not item.get("id") or not item.get("name"):
                skipped += 1
                continue
            # Each product upserts in its own savepoint so one bad row (a slug/SKU
            # clash, odd data) is skipped instead of failing the whole import.
            try:
                with transaction.atomic():
                    was_new = self._upsert(store=store, connection=connection, item=item)
            except Exception as exc:  # noqa: BLE001 — resilient bulk import
                logger.warning("POS import skipped product %s: %s", item.get("id"), exc)
                skipped += 1
                continue
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

    # --- Push a placed order to the cashier (so it shows in the cashier log) ---
    def push_order(self, *, connection: PosSupplierConnection, order) -> dict:
        """Send a confirmed store order to the cashier's order log / revenue. Each
        line is mapped to its **cashier** product id (``external_id`` from the
        import — NOT our store product id), so the cashier recognises it. Idempotent
        on the cashier side via ``external_id`` (the order number), so retries are
        safe.

        Raises rather than pretending success: if no line maps to a cashier product
        the order can't be recorded there, and if the cashier doesn't answer with an
        ``{id}`` we treat it as NOT sent — the caller must never report "sent" on a
        response we didn't confirm.
        """
        store = connection.store
        items = []
        for line in order.items.all():
            product = getattr(line.variant, "product", None)
            if product is None:
                continue
            ref = PosImportedProduct.all_objects.filter(
                store=store, connection=connection, product=product, is_deleted=False
            ).first()
            if ref is None:
                continue  # not a cashier product — can't be recorded there
            items.append(
                {
                    # The cashier's own product id (from GET /integration/products),
                    # not the store product id — otherwise the cashier ignores it.
                    "product_id": ref.external_id,
                    "quantity": line.quantity,
                    "unit_price": float(line.unit_price),
                }
            )
        # Guard: an order whose products aren't linked to the cashier would be
        # recorded there as an empty sale. Fail loudly instead of silently "sending".
        if not items:
            raise ConflictError(
                "None of this order's products are linked to the cashier. "
                "Re-import the cashier catalogue, then try again.",
                code="pos_no_cashier_items",
            )
        address = order.shipping_address if isinstance(order.shipping_address, dict) else {}
        address_str = "، ".join(
            p for p in (address.get("line1"), address.get("line2"), address.get("city"), address.get("region")) if p
        )
        payload = {
            "external_id": order.number,
            "customer_name": address.get("full_name") or "",
            "customer_phone": address.get("phone") or "",
            "address": address_str,
            "notes": order.notes or "",
            "total_amount": float(order.total),
            "tax_amount": float(order.tax_total),
            "discount_amount": float(order.discount_total),
            "payment_method": "ONLINE",
            # Marks this as a fresh online order + when it was placed, so the
            # cashier can surface/alert new arrivals and show their time.
            "source": "online",
            "currency": order.currency or "",
            "placed_at": order.created_at.isoformat() if order.created_at else None,
            "items": items,
        }
        client = self._client(store=store, api_url=connection.api_url, api_key=connection.api_key)
        # The client raises on 401/404/5xx/non-JSON (PosUnavailableError) and on
        # 409 out-of-stock (PosOutOfStockError); a plain 200/201 returns the body.
        result = client.push_order(payload)
        # Only a response carrying an { id } is a real confirmation. Anything else
        # (empty body, no id) means the cashier did NOT record it — don't stamp
        # "synced" and don't let the caller claim success.
        ref = str(result.get("id") or "").strip()
        if not ref:
            raise PosUnavailableError(
                "The cashier accepted the request but returned no order id, so the "
                "order was not confirmed. Please try again."
            )
        order.pos_reference = ref
        order.pos_synced_at = timezone.now()
        order.save(update_fields=["pos_reference", "pos_synced_at", "updated_at"])
        return result

    def check_cashier_stock(self, *, store, lines) -> list:
        """Names of cart lines the linked cashier can't currently fulfil (its live
        stock < requested) — so the buyer sees "unavailable" BEFORE paying. Best
        effort: returns [] when no cashier is linked or it's unreachable (we then
        fall back to our own warehouse checks). ``lines`` = iterable of
        (variant, quantity)."""
        connection = PosSupplierConnection.all_objects.filter(
            store=store, is_connected=True, is_deleted=False
        ).first()
        if connection is None:
            return []
        need = {}  # cashier product id -> [name, requested qty]
        for variant, qty in lines:
            product = getattr(variant, "product", None)
            if product is None:
                continue
            ref = PosImportedProduct.all_objects.filter(
                store=store, connection=connection, product=product, is_deleted=False
            ).first()
            if ref is None:
                continue
            entry = need.setdefault(str(ref.external_id), [product.name, 0])
            entry[1] += int(qty)
        if not need:
            return []
        try:
            products = self._client(
                store=store, api_url=connection.api_url, api_key=connection.api_key
            ).fetch_products()
        except (PosUnavailableError, PosAuthError):
            return []  # can't verify → don't block the sale
        stock_by_id = {
            str(p["id"]): p.get("stock")
            for p in products
            if isinstance(p, dict) and p.get("id") is not None
        }
        out = []
        for ext_id, (name, qty) in need.items():
            available = stock_by_id.get(ext_id)
            if available is not None and int(available) < qty:
                out.append(name)
        return out

    def push_order_for(self, *, store, order) -> dict:
        """Manual (re)send of a paid order to the store's connected cashier. Raises
        a clean error if the order isn't confirmed or no cashier is linked."""
        if order.status in ("pending", "cancelled"):
            raise ConflictError(
                "Only a confirmed order can be sent to the cashier.",
                code="order_not_confirmed",
            )
        connection = PosSupplierConnection.all_objects.filter(
            store=store, is_connected=True, is_deleted=False
        ).first()
        if connection is None:
            raise NotFoundError(
                "No cashier system is connected to this store.", code="no_cashier"
            )
        return self.push_order(connection=connection, order=order)

    # --- Upsert one external product ---
    def _upsert(self, *, store, connection: PosSupplierConnection, item: dict) -> bool:
        external_id = str(item["id"])
        barcode = str(item.get("barcode") or "").strip()
        price = self._decimal(item.get("price"))
        cost = self._decimal(item.get("cost"), allow_none=True)
        stock = self._safe_int(item.get("stock"))
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
    def _safe_int(value) -> int:
        try:
            return max(int(float(value)), 0)
        except (TypeError, ValueError):
            return 0

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
        # The image URL is also a server-side fetch — same SSRF guard as the API URL.
        if not is_public_url(image_url):
            return
        try:
            from apps.pos.client import USER_AGENT

            request = urllib.request.Request(image_url, headers={"User-Agent": USER_AGENT})
            # SSRF-hardened open (re-checks the URL + any redirect target).
            with open_public_url(request, timeout=8) as resp:
                if getattr(resp, "status", 200) != 200:
                    return
                data = resp.read(5 * 1024 * 1024)  # cap at 5 MB
            if not data:
                return
            ext = (image_url.rsplit(".", 1)[-1].split("?")[0] or "jpg")[:5]
            product.image.save(f"pos-{product.id}.{ext}", ContentFile(data), save=True)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            logger.warning("POS image import failed for %s: %s", image_url, exc)
