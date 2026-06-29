"""Inventory scheduled-task tests (P2.10): stale-reservation expiry sweep."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.inventory.models import ReservationStatus, StockItem
from apps.inventory.services import InventoryService
from apps.inventory.tasks import expire_stale_reservations

pytestmark = pytest.mark.django_db


def test_expire_stale_reservations_releases_expired(make_store, make_variant, make_warehouse):
    store, _owner = make_store()
    variant = make_variant(store)
    warehouse = make_warehouse(store)
    inventory = InventoryService()
    inventory.receive(store=store, variant=variant, warehouse=warehouse, quantity=10)
    reservation = inventory.reserve(
        store=store,
        variant=variant,
        warehouse=warehouse,
        quantity=4,
        expires_at=timezone.now() - timedelta(minutes=5),
    )

    assert expire_stale_reservations() == 1
    reservation.refresh_from_db()
    assert reservation.status == ReservationStatus.RELEASED
    item = StockItem.objects.get(store=store, variant=variant, warehouse=warehouse)
    assert item.reserved_quantity == 0
    assert item.available_quantity == 10


def test_unexpired_reservation_is_untouched(make_store, make_variant, make_warehouse):
    store, _owner = make_store()
    variant = make_variant(store)
    warehouse = make_warehouse(store)
    inventory = InventoryService()
    inventory.receive(store=store, variant=variant, warehouse=warehouse, quantity=10)
    reservation = inventory.reserve(
        store=store,
        variant=variant,
        warehouse=warehouse,
        quantity=4,
        expires_at=timezone.now() + timedelta(hours=1),
    )

    assert expire_stale_reservations() == 0
    reservation.refresh_from_db()
    assert reservation.status == ReservationStatus.ACTIVE
