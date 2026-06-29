"""Procurement application service: suppliers, purchase orders, batches, serials.

Receiving a purchase order is the one operation that turns a vendor order into
on-hand stock: it delegates the quantity change to ``InventoryService.receive``
(row-locked, ledgered) and records a :class:`StockBatch` lot for traceability.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from django.db.models import F
from django.utils import timezone
from django.utils.text import slugify

from apps.core.exceptions import BusinessRuleError, ConflictError, NotFoundError, ValidationError
from apps.core.services import BaseService, atomic
from apps.inventory.services import InventoryService
from apps.procurement.models import (
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseOrderStatus,
    SerialNumber,
    StockBatch,
    Supplier,
)

_CENTS = Decimal("0.01")


def _money(value) -> Decimal:
    return Decimal(value).quantize(_CENTS, rounding=ROUND_HALF_UP)


class ProcurementService(BaseService):
    def __init__(self, inventory: InventoryService | None = None) -> None:
        self.inventory = inventory or InventoryService()

    # --- Suppliers ---
    @atomic
    def create_supplier(self, *, store, data: dict) -> Supplier:
        code = (data.get("code") or "").strip() or self._unique_supplier_code(
            store=store, name=data["name"]
        )
        if Supplier.all_objects.filter(store=store, code=code, is_deleted=False).exists():
            raise ConflictError("A supplier with this code already exists.", code="code_taken")
        payload = {k: v for k, v in data.items() if k != "code"}
        return Supplier.objects.create(store=store, code=code, **payload)

    @atomic
    def update_supplier(self, *, instance: Supplier, data: dict) -> Supplier:
        if data.get("code"):
            code = data["code"].strip()
            if (
                Supplier.all_objects.filter(store=instance.store, code=code, is_deleted=False)
                .exclude(pk=instance.pk)
                .exists()
            ):
                raise ConflictError("A supplier with this code already exists.", code="code_taken")
        for field, value in data.items():
            setattr(instance, field, value)
        instance.save()
        return instance

    # --- Purchase orders ---
    @atomic
    def create_po(
        self, *, store, supplier, warehouse, lines: list[dict], **header
    ) -> PurchaseOrder:
        if not lines:
            raise ValidationError("A purchase order needs at least one line.", code="empty_po")
        po = PurchaseOrder.objects.create(
            store=store,
            supplier=supplier,
            warehouse=warehouse,
            number=self._generate_number(store),
            status=PurchaseOrderStatus.DRAFT,
            **header,
        )
        subtotal = Decimal("0.00")
        for line in lines:
            unit_cost = _money(line.get("unit_cost", 0))
            quantity = int(line["quantity_ordered"])
            if quantity <= 0:
                raise ValidationError("Line quantity must be positive.")
            PurchaseOrderLine.objects.create(
                store=store,
                purchase_order=po,
                variant=line["variant"],
                quantity_ordered=quantity,
                unit_cost=unit_cost,
                batch_number=line.get("batch_number", "") or "",
                expiry_date=line.get("expiry_date"),
            )
            subtotal += unit_cost * quantity
        po.subtotal = _money(subtotal)
        po.save(update_fields=["subtotal", "updated_at"])
        return po

    @atomic
    def submit_po(self, *, po: PurchaseOrder) -> PurchaseOrder:
        if po.status != PurchaseOrderStatus.DRAFT:
            raise ConflictError("Only a draft purchase order can be submitted.", code="not_draft")
        if not po.lines.exists():
            raise ValidationError("Cannot submit a purchase order with no lines.")
        po.status = PurchaseOrderStatus.SUBMITTED
        po.save(update_fields=["status", "updated_at"])
        return po

    @atomic
    def receive_po(self, *, po: PurchaseOrder, receipts: dict | None = None) -> PurchaseOrder:
        """Receive a submitted PO into its warehouse.

        ``receipts`` maps line id -> quantity for partial receipts; when omitted,
        every line's outstanding quantity is received in full.
        """
        if po.status != PurchaseOrderStatus.SUBMITTED:
            raise ConflictError(
                "Only a submitted purchase order can be received.", code="not_submitted"
            )
        lines = list(po.lines.select_related("variant"))
        for line in lines:
            quantity = (
                line.quantity_outstanding
                if receipts is None
                else int(receipts.get(str(line.id), 0))
            )
            if quantity <= 0:
                continue
            if quantity > line.quantity_outstanding:
                raise BusinessRuleError(
                    "Cannot receive more than the outstanding quantity.", code="over_receipt"
                )
            self.inventory.receive(
                store=po.store,
                variant=line.variant,
                warehouse=po.warehouse,
                quantity=quantity,
                reference=f"po:{po.number}",
            )
            line.quantity_received += quantity
            line.save(update_fields=["quantity_received", "updated_at"])
            self._record_batch(po=po, line=line, quantity=quantity)

        if all(line.quantity_outstanding == 0 for line in lines):
            po.status = PurchaseOrderStatus.RECEIVED
            po.received_at = timezone.now()
            po.save(update_fields=["status", "received_at", "updated_at"])
        return po

    @atomic
    def cancel_po(self, *, po: PurchaseOrder) -> PurchaseOrder:
        if po.status == PurchaseOrderStatus.RECEIVED:
            raise ConflictError("A received purchase order cannot be cancelled.", code="received")
        po.status = PurchaseOrderStatus.CANCELLED
        po.save(update_fields=["status", "updated_at"])
        return po

    # --- Batches / expiry ---
    def expiring_batches(self, *, store, before_date):
        return StockBatch.objects.filter(
            store=store, quantity__gt=0, expiry_date__isnull=False, expiry_date__lte=before_date
        )

    @atomic
    def consume_batches_fefo(self, *, store, variant, warehouse, quantity: int) -> int:
        """Deplete lots first-expiry-first as stock leaves a warehouse.

        Best-effort traceability layered on the aggregate ``StockItem`` (which
        remains the source of truth): variants stocked without batches are a
        no-op. Returns the quantity actually attributed to batches.
        """
        remaining = quantity
        batches = (
            StockBatch.objects.select_for_update()
            .filter(store=store, variant=variant, warehouse=warehouse, quantity__gt=0)
            .order_by(F("expiry_date").asc(nulls_last=True), "created_at")
        )
        for batch in batches:
            if remaining <= 0:
                break
            take = min(batch.quantity, remaining)
            batch.quantity -= take
            batch.save(update_fields=["quantity", "updated_at"])
            remaining -= take
        return quantity - remaining

    def _record_batch(self, *, po: PurchaseOrder, line: PurchaseOrderLine, quantity: int) -> None:
        batch_number = line.batch_number or po.number
        batch, created = StockBatch.objects.get_or_create(
            store=po.store,
            variant=line.variant,
            warehouse=po.warehouse,
            batch_number=batch_number,
            defaults={
                "quantity": quantity,
                "expiry_date": line.expiry_date,
                "purchase_order": po,
            },
        )
        if not created:
            batch.quantity += quantity
            if line.expiry_date and not batch.expiry_date:
                batch.expiry_date = line.expiry_date
            batch.save(update_fields=["quantity", "expiry_date", "updated_at"])

    # --- Serial numbers ---
    @atomic
    def register_serials(self, *, store, variant, warehouse, serials: list[str], batch=None):
        created = []
        for raw in serials:
            serial = raw.strip()
            if not serial:
                continue
            if SerialNumber.all_objects.filter(
                store=store, variant=variant, serial=serial, is_deleted=False
            ).exists():
                raise ConflictError(f"Serial '{serial}' already exists.", code="serial_exists")
            created.append(
                SerialNumber.objects.create(
                    store=store, variant=variant, warehouse=warehouse, serial=serial, batch=batch
                )
            )
        if not created:
            raise ValidationError("Provide at least one serial number.")
        return created

    @atomic
    def set_serial_status(self, *, serial: SerialNumber, status: str) -> SerialNumber:
        serial.status = status
        serial.save(update_fields=["status", "updated_at"])
        return serial

    # --- Helpers ---
    @staticmethod
    def get_po(*, store, po_id) -> PurchaseOrder:
        po = PurchaseOrder.objects.filter(store=store, id=po_id).first()
        if po is None:
            raise NotFoundError("Purchase order not found.")
        return po

    @staticmethod
    def _generate_number(store) -> str:
        sequence = PurchaseOrder.all_objects.filter(store=store).count() + 1
        return f"PO-{sequence:06d}"

    @staticmethod
    def _unique_supplier_code(*, store, name: str) -> str:
        base = slugify(name)[:50] or "supplier"
        code = base
        suffix = 1
        while Supplier.all_objects.filter(store=store, code=code, is_deleted=False).exists():
            suffix += 1
            code = f"{base}-{suffix}"
        return code
