"""Reservation lifecycle (service-level): reserve / release / commit."""

from __future__ import annotations

import pytest

from apps.core.exceptions import BusinessRuleError, ConflictError
from apps.inventory.models import ReservationStatus, StockItem, StockMovementType
from apps.inventory.services import InventoryService

pytestmark = pytest.mark.django_db


def _seed(store, variant, warehouse, qty):
    return InventoryService().receive(
        store=store, variant=variant, warehouse=warehouse, quantity=qty
    )


def test_reserve_holds_available_stock(make_store, make_variant, make_warehouse):
    store, _ = make_store()
    variant = make_variant(store)
    warehouse = make_warehouse(store)
    _seed(store, variant, warehouse, 10)

    reservation = InventoryService().reserve(
        store=store, variant=variant, warehouse=warehouse, quantity=4, reference="cart:1"
    )
    item = StockItem.objects.get(variant=variant, warehouse=warehouse)
    assert item.reserved_quantity == 4
    assert item.available_quantity == 6
    assert reservation.status == ReservationStatus.ACTIVE


def test_cannot_reserve_more_than_available(make_store, make_variant, make_warehouse):
    store, _ = make_store()
    variant = make_variant(store)
    warehouse = make_warehouse(store)
    _seed(store, variant, warehouse, 5)
    with pytest.raises(BusinessRuleError):
        InventoryService().reserve(store=store, variant=variant, warehouse=warehouse, quantity=6)


def test_release_frees_reservation(make_store, make_variant, make_warehouse):
    store, _ = make_store()
    variant = make_variant(store)
    warehouse = make_warehouse(store)
    _seed(store, variant, warehouse, 10)
    service = InventoryService()
    reservation = service.reserve(store=store, variant=variant, warehouse=warehouse, quantity=4)
    service.release(reservation=reservation)

    item = StockItem.objects.get(variant=variant, warehouse=warehouse)
    assert item.reserved_quantity == 0
    assert item.available_quantity == 10
    reservation.refresh_from_db()
    assert reservation.status == ReservationStatus.RELEASED


def test_commit_deducts_stock_and_logs_sale(make_store, make_variant, make_warehouse):
    store, _ = make_store()
    variant = make_variant(store)
    warehouse = make_warehouse(store)
    _seed(store, variant, warehouse, 10)
    service = InventoryService()
    reservation = service.reserve(store=store, variant=variant, warehouse=warehouse, quantity=4)
    service.commit(reservation=reservation)

    item = StockItem.objects.get(variant=variant, warehouse=warehouse)
    assert item.quantity == 6
    assert item.reserved_quantity == 0
    reservation.refresh_from_db()
    assert reservation.status == ReservationStatus.COMMITTED
    assert variant.stock_movements.filter(movement_type=StockMovementType.SALE).exists()


def test_cannot_commit_released_reservation(make_store, make_variant, make_warehouse):
    store, _ = make_store()
    variant = make_variant(store)
    warehouse = make_warehouse(store)
    _seed(store, variant, warehouse, 10)
    service = InventoryService()
    reservation = service.reserve(store=store, variant=variant, warehouse=warehouse, quantity=4)
    service.release(reservation=reservation)
    with pytest.raises(ConflictError):
        service.commit(reservation=reservation)
