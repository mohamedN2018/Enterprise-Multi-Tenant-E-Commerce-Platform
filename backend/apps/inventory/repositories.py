"""Inventory repositories (queries run through tenant-scoped managers)."""

from __future__ import annotations

from apps.core.repositories import BaseRepository
from apps.inventory.models import StockItem, StockMovement, Warehouse


class WarehouseRepository(BaseRepository[Warehouse]):
    model = Warehouse


class StockItemRepository(BaseRepository[StockItem]):
    model = StockItem

    def with_relations(self):
        return self.get_queryset().select_related("variant", "warehouse")

    def low_stock(self):
        # available = quantity - reserved <= reorder_point
        from django.db.models import F

        return self.get_queryset().filter(quantity__lte=F("reserved_quantity") + F("reorder_point"))


class StockMovementRepository(BaseRepository[StockMovement]):
    model = StockMovement
