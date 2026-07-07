"""Inventory application service.

All quantity mutations acquire a row lock on the affected ``StockItem``
(``select_for_update`` inside ``transaction.atomic``) to prevent oversell under
concurrency, and write an append-only ``StockMovement`` ledger entry. On
PostgreSQL the lock is real; on SQLite (tests) it is a no-op.
"""

from __future__ import annotations

from apps.core.exceptions import BusinessRuleError, ConflictError, NotFoundError, ValidationError
from apps.core.services import BaseService, atomic
from apps.core.signals import stock_committed
from apps.inventory.models import (
    ReservationStatus,
    StockItem,
    StockMovement,
    StockMovementType,
    StockReservation,
    Warehouse,
)


class InventoryService(BaseService):
    # --- Stock items ---
    def get_or_create_item(self, *, store, variant, warehouse) -> StockItem:
        item, _ = StockItem.objects.get_or_create(store=store, variant=variant, warehouse=warehouse)
        return item

    def _locked_item(self, *, store, variant, warehouse, create: bool) -> StockItem:
        item = (
            StockItem.objects.select_for_update()
            .filter(store=store, variant=variant, warehouse=warehouse)
            .first()
        )
        if item is None:
            if not create:
                raise NotFoundError("No stock record exists for this variant/warehouse.")
            StockItem.objects.create(store=store, variant=variant, warehouse=warehouse)
            item = StockItem.objects.select_for_update().get(
                store=store, variant=variant, warehouse=warehouse
            )
        return item

    def _log(
        self,
        *,
        store,
        item: StockItem,
        movement_type: str,
        quantity_change: int,
        reserved_change: int = 0,
        reference: str = "",
        note: str = "",
    ) -> StockMovement:
        return StockMovement.objects.create(
            store=store,
            variant=item.variant,
            warehouse=item.warehouse,
            movement_type=movement_type,
            quantity_change=quantity_change,
            reserved_change=reserved_change,
            resulting_quantity=item.quantity,
            reference=reference,
            note=note,
        )

    # --- Operations ---
    @atomic
    def receive(
        self, *, store, variant, warehouse, quantity: int, reference: str = "", note: str = ""
    ) -> StockItem:
        if quantity <= 0:
            raise ValidationError("Quantity to receive must be positive.")
        item = self._locked_item(store=store, variant=variant, warehouse=warehouse, create=True)
        item.quantity += quantity
        item.save(update_fields=["quantity", "updated_at"])
        self._log(
            store=store,
            item=item,
            movement_type=StockMovementType.RECEIPT,
            quantity_change=quantity,
            reference=reference,
            note=note,
        )
        return item

    @atomic
    def adjust(self, *, store, variant, warehouse, new_quantity: int, note: str = "") -> StockItem:
        if new_quantity < 0:
            raise ValidationError("Quantity cannot be negative.")
        item = self._locked_item(store=store, variant=variant, warehouse=warehouse, create=True)
        if new_quantity < item.reserved_quantity:
            raise BusinessRuleError("Cannot set quantity below the currently reserved amount.")
        delta = new_quantity - item.quantity
        item.quantity = new_quantity
        item.save(update_fields=["quantity", "updated_at"])
        self._log(
            store=store,
            item=item,
            movement_type=StockMovementType.ADJUSTMENT,
            quantity_change=delta,
            note=note,
        )
        return item

    @atomic
    def transfer(
        self, *, store, variant, from_warehouse, to_warehouse, quantity: int, note: str = ""
    ) -> tuple[StockItem, StockItem]:
        if quantity <= 0:
            raise ValidationError("Transfer quantity must be positive.")
        if from_warehouse == to_warehouse:
            raise ValidationError("Source and destination warehouses must differ.")
        source = self._locked_item(
            store=store, variant=variant, warehouse=from_warehouse, create=False
        )
        if source.available_quantity < quantity:
            raise BusinessRuleError("Insufficient available stock to transfer.")
        destination = self._locked_item(
            store=store, variant=variant, warehouse=to_warehouse, create=True
        )

        source.quantity -= quantity
        source.save(update_fields=["quantity", "updated_at"])
        destination.quantity += quantity
        destination.save(update_fields=["quantity", "updated_at"])

        self._log(
            store=store,
            item=source,
            movement_type=StockMovementType.TRANSFER_OUT,
            quantity_change=-quantity,
            reference=f"warehouse:{to_warehouse.id}",
            note=note,
        )
        self._log(
            store=store,
            item=destination,
            movement_type=StockMovementType.TRANSFER_IN,
            quantity_change=quantity,
            reference=f"warehouse:{from_warehouse.id}",
            note=note,
        )
        return source, destination

    # --- Reservations (used by cart/checkout) ---
    @atomic
    def reserve(
        self, *, store, variant, warehouse, quantity: int, reference: str = "", expires_at=None
    ) -> StockReservation:
        if quantity <= 0:
            raise ValidationError("Reservation quantity must be positive.")
        item = self._locked_item(store=store, variant=variant, warehouse=warehouse, create=True)
        if item.available_quantity < quantity:
            raise BusinessRuleError("Insufficient available stock to reserve.")
        item.reserved_quantity += quantity
        item.save(update_fields=["reserved_quantity", "updated_at"])
        reservation = StockReservation.objects.create(
            store=store,
            variant=variant,
            warehouse=warehouse,
            quantity=quantity,
            reference=reference,
            status=ReservationStatus.ACTIVE,
            expires_at=expires_at,
        )
        self._log(
            store=store,
            item=item,
            movement_type=StockMovementType.RESERVATION,
            quantity_change=0,
            reserved_change=quantity,
            reference=reference,
        )
        return reservation

    @atomic
    def release(self, *, reservation: StockReservation) -> None:
        if reservation.status != ReservationStatus.ACTIVE:
            return  # idempotent
        item = self._locked_item(
            store=reservation.store,
            variant=reservation.variant,
            warehouse=reservation.warehouse,
            create=True,
        )
        item.reserved_quantity = max(0, item.reserved_quantity - reservation.quantity)
        item.save(update_fields=["reserved_quantity", "updated_at"])
        reservation.status = ReservationStatus.RELEASED
        reservation.save(update_fields=["status", "updated_at"])
        self._log(
            store=reservation.store,
            item=item,
            movement_type=StockMovementType.RELEASE,
            quantity_change=0,
            reserved_change=-reservation.quantity,
            reference=reservation.reference,
        )

    @atomic
    def commit(self, *, reservation: StockReservation) -> None:
        """Convert an active reservation into an actual stock deduction (a sale)."""
        if reservation.status != ReservationStatus.ACTIVE:
            raise ConflictError("Only an active reservation can be committed.")
        item = self._locked_item(
            store=reservation.store,
            variant=reservation.variant,
            warehouse=reservation.warehouse,
            create=True,
        )
        qty = reservation.quantity
        item.quantity = max(0, item.quantity - qty)
        item.reserved_quantity = max(0, item.reserved_quantity - qty)
        item.save(update_fields=["quantity", "reserved_quantity", "updated_at"])
        reservation.status = ReservationStatus.COMMITTED
        reservation.save(update_fields=["status", "updated_at"])
        self._log(
            store=reservation.store,
            item=item,
            movement_type=StockMovementType.SALE,
            quantity_change=-qty,
            reserved_change=-qty,
            reference=reservation.reference,
        )
        stock_committed.send(
            sender=self.__class__,
            store=reservation.store,
            variant=reservation.variant,
            warehouse=reservation.warehouse,
            quantity=qty,
            reference=reservation.reference,
        )

    @atomic
    def issue(
        self, *, store, variant, warehouse, quantity: int, reference: str = "", note: str = ""
    ) -> StockItem:
        """Deduct on-hand stock for a non-sale reason (e.g. production consumption)."""
        if quantity <= 0:
            raise ValidationError("Quantity to issue must be positive.")
        item = self._locked_item(store=store, variant=variant, warehouse=warehouse, create=False)
        if item.available_quantity < quantity:
            raise BusinessRuleError(
                "Insufficient available stock to issue.", code="insufficient_stock"
            )
        item.quantity -= quantity
        item.save(update_fields=["quantity", "updated_at"])
        self._log(
            store=store,
            item=item,
            movement_type=StockMovementType.ADJUSTMENT,
            quantity_change=-quantity,
            reference=reference,
            note=note,
        )
        stock_committed.send(
            sender=self.__class__,
            store=store,
            variant=variant,
            warehouse=warehouse,
            quantity=quantity,
            reference=reference,
        )
        return item

    # --- Warehouse helper ---
    @staticmethod
    def default_warehouse(*, store) -> Warehouse:
        """The store's stock-keeping warehouse, creating it on first use so a new
        store can hold stock immediately. Prefer the flagged default, else MAIN."""
        warehouse = (
            Warehouse.objects.filter(store=store, is_default=True).first()
            or Warehouse.objects.filter(store=store, code="MAIN").first()
        )
        if warehouse is None:
            warehouse = Warehouse.objects.create(
                store=store, code="MAIN", name="Main Warehouse", is_default=True
            )
        return warehouse

    @staticmethod
    def ensure_single_default(*, store, warehouse: Warehouse) -> None:
        if warehouse.is_default:
            Warehouse.objects.filter(store=store, is_default=True).exclude(pk=warehouse.pk).update(
                is_default=False
            )
