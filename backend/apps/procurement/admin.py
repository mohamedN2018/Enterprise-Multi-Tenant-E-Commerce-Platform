"""Admin registration for procurement."""

from __future__ import annotations

from django.contrib import admin

from apps.procurement.models import (
    BillOfMaterials,
    BOMComponent,
    PurchaseOrder,
    PurchaseOrderLine,
    SerialNumber,
    StockBatch,
    Supplier,
    WorkOrder,
)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "store", "email", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code", "store__name")


class PurchaseOrderLineInline(admin.TabularInline):
    model = PurchaseOrderLine
    extra = 0
    fields = (
        "variant",
        "quantity_ordered",
        "quantity_received",
        "unit_cost",
        "batch_number",
        "expiry_date",
    )
    raw_id_fields = ("variant",)


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ("number", "store", "supplier", "warehouse", "status", "subtotal", "received_at")
    list_filter = ("status",)
    search_fields = ("number", "supplier__name", "store__name")
    inlines = (PurchaseOrderLineInline,)


@admin.register(StockBatch)
class StockBatchAdmin(admin.ModelAdmin):
    list_display = ("batch_number", "store", "variant", "warehouse", "quantity", "expiry_date")
    list_filter = ("expiry_date",)
    search_fields = ("batch_number", "store__name")


@admin.register(SerialNumber)
class SerialNumberAdmin(admin.ModelAdmin):
    list_display = ("serial", "store", "variant", "warehouse", "status")
    list_filter = ("status",)
    search_fields = ("serial", "store__name")


class BOMComponentInline(admin.TabularInline):
    model = BOMComponent
    extra = 0
    fields = ("component_variant", "quantity")
    raw_id_fields = ("component_variant",)


@admin.register(BillOfMaterials)
class BillOfMaterialsAdmin(admin.ModelAdmin):
    list_display = ("name", "store", "output_variant", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "store__name")
    inlines = (BOMComponentInline,)


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ("number", "store", "bom", "warehouse", "quantity", "status", "completed_at")
    list_filter = ("status",)
    search_fields = ("number", "store__name")
