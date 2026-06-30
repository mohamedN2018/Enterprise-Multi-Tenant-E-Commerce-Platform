"""Inventory domain models (store-scoped via ``TenantOwnedModel``).

This is the source of truth for stock, superseding ``ProductVariant.stock_quantity``.

* ``Warehouse``        — a stock location within a store.
* ``StockItem``        — on-hand + reserved quantity for a (variant, warehouse).
* ``StockMovement``    — append-only ledger of every quantity change.
* ``StockReservation`` — a hold placed on stock for a cart/order.

All quantity mutations go through ``InventoryService`` under row locks; models
here only describe state and derived read-only properties.
"""

from __future__ import annotations

from django.db import models
from django.db.models import Q

from apps.core.models import TenantOwnedModel


class Warehouse(TenantOwnedModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=2, blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Warehouse"
        verbose_name_plural = "Warehouses"
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["store", "code"],
                condition=Q(is_deleted=False),
                name="uniq_warehouse_store_code",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class StockItem(TenantOwnedModel):
    variant = models.ForeignKey(
        "catalog.ProductVariant", on_delete=models.CASCADE, related_name="stock_items"
    )
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="stock_items")
    quantity = models.PositiveIntegerField(default=0)
    reserved_quantity = models.PositiveIntegerField(default=0)
    reorder_point = models.PositiveIntegerField(default=0)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Stock item"
        verbose_name_plural = "Stock items"
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["store", "variant", "warehouse"],
                condition=Q(is_deleted=False),
                name="uniq_stock_variant_warehouse",
            )
        ]
        indexes = [models.Index(fields=["store", "warehouse"])]

    def __str__(self) -> str:
        return f"{self.variant_id} @ {self.warehouse_id}: {self.quantity}"

    @property
    def available_quantity(self) -> int:
        return max(self.quantity - self.reserved_quantity, 0)

    @property
    def is_out_of_stock(self) -> bool:
        return self.available_quantity <= 0

    @property
    def is_low_stock(self) -> bool:
        return self.available_quantity <= self.reorder_point


class StockMovementType(models.TextChoices):
    RECEIPT = "receipt", "Receipt"
    SALE = "sale", "Sale"
    ADJUSTMENT = "adjustment", "Adjustment"
    TRANSFER_IN = "transfer_in", "Transfer in"
    TRANSFER_OUT = "transfer_out", "Transfer out"
    RESERVATION = "reservation", "Reservation"
    RELEASE = "release", "Release"
    RETURN = "return", "Return"


class StockMovement(TenantOwnedModel):
    variant = models.ForeignKey(
        "catalog.ProductVariant", on_delete=models.CASCADE, related_name="stock_movements"
    )
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="stock_movements"
    )
    movement_type = models.CharField(
        max_length=16, choices=StockMovementType.choices, db_index=True
    )
    # Signed deltas applied by this movement.
    quantity_change = models.IntegerField(default=0)
    reserved_change = models.IntegerField(default=0)
    # On-hand quantity after the movement (audit snapshot).
    resulting_quantity = models.PositiveIntegerField()
    reference = models.CharField(max_length=255, blank=True)
    note = models.TextField(blank=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Stock movement"
        verbose_name_plural = "Stock movements"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["variant", "warehouse"]),
            models.Index(fields=["store", "movement_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.movement_type} {self.quantity_change:+d} -> {self.resulting_quantity}"


class ReservationStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    RELEASED = "released", "Released"
    COMMITTED = "committed", "Committed"


class StockReservation(TenantOwnedModel):
    variant = models.ForeignKey(
        "catalog.ProductVariant", on_delete=models.CASCADE, related_name="reservations"
    )
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="reservations")
    quantity = models.PositiveIntegerField()
    reference = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=16,
        choices=ReservationStatus.choices,
        default=ReservationStatus.ACTIVE,
        db_index=True,
    )
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Stock reservation"
        verbose_name_plural = "Stock reservations"
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["store", "status"])]

    def __str__(self) -> str:
        return f"reserve {self.quantity} of {self.variant_id} [{self.status}]"

    @property
    def is_active(self) -> bool:
        return self.status == ReservationStatus.ACTIVE
