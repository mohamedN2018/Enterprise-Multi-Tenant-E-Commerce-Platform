"""Procurement & advanced-inventory models (store-scoped via ``TenantOwnedModel``).

The supply side of the catalog, layered additively on top of ``apps.inventory``:

* ``Supplier``                       — a vendor the store buys from.
* ``PurchaseOrder`` / ``...Line``    — an order to a supplier, received into a
  warehouse (draft → submitted → received), updating stock via ``InventoryService``.
* ``StockBatch``                     — a received lot (batch/expiry traceability).
* ``SerialNumber``                   — a unit-level serial record.

Receiving a purchase order is the single place that turns a vendor order into
on-hand stock; batch and serial records provide traceability on top of the
aggregate ``StockItem`` quantity. (Batch-level FEFO *consumption* at checkout is
a forward step; batches here record what was received and when it expires.)
"""

from __future__ import annotations

from decimal import Decimal

from django.db import models
from django.db.models import Q

from apps.core.models import TenantOwnedModel


class Supplier(TenantOwnedModel):
    name = models.CharField(max_length=255)
    code = models.SlugField(max_length=60)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Supplier"
        verbose_name_plural = "Suppliers"
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["store", "code"],
                condition=Q(is_deleted=False),
                name="uniq_supplier_store_code",
            )
        ]

    def __str__(self) -> str:
        return self.name


class PurchaseOrderStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SUBMITTED = "submitted", "Submitted"
    RECEIVED = "received", "Received"
    CANCELLED = "cancelled", "Cancelled"


class PurchaseOrder(TenantOwnedModel):
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchase_orders")
    warehouse = models.ForeignKey(
        "inventory.Warehouse", on_delete=models.PROTECT, related_name="purchase_orders"
    )
    number = models.CharField(max_length=40)
    status = models.CharField(
        max_length=12,
        choices=PurchaseOrderStatus.choices,
        default=PurchaseOrderStatus.DRAFT,
        db_index=True,
    )
    expected_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    received_at = models.DateTimeField(null=True, blank=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Purchase order"
        verbose_name_plural = "Purchase orders"
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["store", "number"],
                condition=Q(is_deleted=False),
                name="uniq_po_store_number",
            )
        ]
        indexes = [models.Index(fields=["store", "status"])]

    def __str__(self) -> str:
        return self.number


class PurchaseOrderLine(TenantOwnedModel):
    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.CASCADE, related_name="lines"
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant", on_delete=models.PROTECT, related_name="+"
    )
    quantity_ordered = models.PositiveIntegerField()
    quantity_received = models.PositiveIntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    batch_number = models.CharField(max_length=60, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Purchase order line"
        verbose_name_plural = "Purchase order lines"
        ordering = ("created_at",)

    def __str__(self) -> str:
        return f"{self.quantity_ordered} x {self.variant_id}"

    @property
    def line_total(self) -> Decimal:
        return self.unit_cost * self.quantity_ordered

    @property
    def quantity_outstanding(self) -> int:
        return max(self.quantity_ordered - self.quantity_received, 0)


class StockBatch(TenantOwnedModel):
    """A received lot of a variant in a warehouse, with optional expiry."""

    variant = models.ForeignKey(
        "catalog.ProductVariant", on_delete=models.CASCADE, related_name="batches"
    )
    warehouse = models.ForeignKey(
        "inventory.Warehouse", on_delete=models.CASCADE, related_name="batches"
    )
    batch_number = models.CharField(max_length=60)
    quantity = models.PositiveIntegerField(default=0)
    expiry_date = models.DateField(null=True, blank=True, db_index=True)
    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name="batches"
    )

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Stock batch"
        verbose_name_plural = "Stock batches"
        ordering = ("expiry_date", "-created_at")
        constraints = [
            models.UniqueConstraint(
                fields=["store", "variant", "warehouse", "batch_number"],
                condition=Q(is_deleted=False),
                name="uniq_batch_variant_warehouse_number",
            )
        ]

    def __str__(self) -> str:
        return f"{self.batch_number}: {self.quantity}"


class SerialStatus(models.TextChoices):
    IN_STOCK = "in_stock", "In stock"
    SOLD = "sold", "Sold"
    RETURNED = "returned", "Returned"
    DEFECTIVE = "defective", "Defective"


class SerialNumber(TenantOwnedModel):
    variant = models.ForeignKey(
        "catalog.ProductVariant", on_delete=models.CASCADE, related_name="serials"
    )
    warehouse = models.ForeignKey(
        "inventory.Warehouse", on_delete=models.CASCADE, related_name="serials"
    )
    serial = models.CharField(max_length=120)
    status = models.CharField(
        max_length=12, choices=SerialStatus.choices, default=SerialStatus.IN_STOCK, db_index=True
    )
    batch = models.ForeignKey(
        StockBatch, on_delete=models.SET_NULL, null=True, blank=True, related_name="serials"
    )

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Serial number"
        verbose_name_plural = "Serial numbers"
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["store", "variant", "serial"],
                condition=Q(is_deleted=False),
                name="uniq_serial_variant",
            )
        ]

    def __str__(self) -> str:
        return self.serial
