"""Admin registration for inventory models."""

from __future__ import annotations

from django.contrib import admin

from apps.inventory.models import StockItem, StockMovement, StockReservation, Warehouse


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "store", "is_default", "is_active")
    list_filter = ("is_active", "is_default")
    search_fields = ("name", "code", "store__name")


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = (
        "variant",
        "warehouse",
        "store",
        "quantity",
        "reserved_quantity",
        "reorder_point",
    )
    search_fields = ("variant__sku", "warehouse__code", "store__name")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        "movement_type",
        "variant",
        "warehouse",
        "quantity_change",
        "resulting_quantity",
        "created_at",
    )
    list_filter = ("movement_type",)
    search_fields = ("variant__sku", "warehouse__code", "reference")
    readonly_fields = [f.name for f in StockMovement._meta.fields]


@admin.register(StockReservation)
class StockReservationAdmin(admin.ModelAdmin):
    list_display = ("variant", "warehouse", "quantity", "status", "reference", "created_at")
    list_filter = ("status",)
    search_fields = ("variant__sku", "reference")
