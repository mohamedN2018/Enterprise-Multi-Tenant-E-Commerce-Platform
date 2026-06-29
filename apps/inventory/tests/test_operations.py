"""Stock operation tests: receive / adjust / transfer + isolation + low-stock."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.inventory.models import StockItem, StockMovement, StockMovementType

pytestmark = pytest.mark.django_db

RECEIVE = reverse("v1:inventory:stock-receive")
ADJUST = reverse("v1:inventory:stock-adjust")
TRANSFER = reverse("v1:inventory:stock-transfer")
STOCK_LIST = reverse("v1:inventory:stock-list")
LOW_STOCK = reverse("v1:inventory:stock-low")


def test_receive_increments_and_logs(store_client, make_store, make_variant, make_warehouse):
    store, owner = make_store()
    variant = make_variant(store)
    warehouse = make_warehouse(store)
    client = store_client(owner, store)

    resp = client.post(
        RECEIVE,
        {"variant_id": str(variant.id), "warehouse_id": str(warehouse.id), "quantity": 10},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["quantity"] == 10

    client.post(
        RECEIVE,
        {"variant_id": str(variant.id), "warehouse_id": str(warehouse.id), "quantity": 5},
        format="json",
    )
    item = StockItem.objects.get(variant=variant, warehouse=warehouse)
    assert item.quantity == 15
    assert (
        StockMovement.objects.filter(
            variant=variant, movement_type=StockMovementType.RECEIPT
        ).count()
        == 2
    )


def test_adjust_sets_absolute_quantity(store_client, make_store, make_variant, make_warehouse):
    store, owner = make_store()
    variant = make_variant(store)
    warehouse = make_warehouse(store)
    client = store_client(owner, store)
    client.post(
        RECEIVE,
        {"variant_id": str(variant.id), "warehouse_id": str(warehouse.id), "quantity": 10},
        format="json",
    )
    resp = client.post(
        ADJUST,
        {"variant_id": str(variant.id), "warehouse_id": str(warehouse.id), "quantity": 3},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["quantity"] == 3


def test_transfer_moves_stock(store_client, make_store, make_variant, make_warehouse):
    store, owner = make_store()
    variant = make_variant(store)
    wh1 = make_warehouse(store, code="W1")
    wh2 = make_warehouse(store, code="W2")
    client = store_client(owner, store)
    client.post(
        RECEIVE,
        {"variant_id": str(variant.id), "warehouse_id": str(wh1.id), "quantity": 10},
        format="json",
    )
    resp = client.post(
        TRANSFER,
        {
            "variant_id": str(variant.id),
            "from_warehouse_id": str(wh1.id),
            "to_warehouse_id": str(wh2.id),
            "quantity": 4,
        },
        format="json",
    )
    assert resp.status_code == 200
    assert StockItem.objects.get(variant=variant, warehouse=wh1).quantity == 6
    assert StockItem.objects.get(variant=variant, warehouse=wh2).quantity == 4


def test_transfer_insufficient_stock(store_client, make_store, make_variant, make_warehouse):
    store, owner = make_store()
    variant = make_variant(store)
    wh1 = make_warehouse(store, code="W1")
    wh2 = make_warehouse(store, code="W2")
    client = store_client(owner, store)
    client.post(
        RECEIVE,
        {"variant_id": str(variant.id), "warehouse_id": str(wh1.id), "quantity": 3},
        format="json",
    )
    resp = client.post(
        TRANSFER,
        {
            "variant_id": str(variant.id),
            "from_warehouse_id": str(wh1.id),
            "to_warehouse_id": str(wh2.id),
            "quantity": 10,
        },
        format="json",
    )
    assert resp.status_code == 422


def test_receive_requires_write_role(
    store_client, make_store, make_variant, make_warehouse, make_user, add_member
):
    from apps.stores.models import StoreRole

    store, _owner = make_store()
    variant = make_variant(store)
    warehouse = make_warehouse(store)
    employee = make_user()
    add_member(store, employee, StoreRole.EMPLOYEE)
    resp = store_client(employee, store).post(
        RECEIVE,
        {"variant_id": str(variant.id), "warehouse_id": str(warehouse.id), "quantity": 5},
        format="json",
    )
    assert resp.status_code == 403


def test_store_context_required(make_store):
    _store, owner = make_store()
    client = APIClient()
    client.force_authenticate(user=owner)
    assert client.get(STOCK_LIST).status_code == 400


def test_stock_is_store_scoped(store_client, make_store, make_variant, make_warehouse):
    store_a, owner_a = make_store(name="A")
    store_b, owner_b = make_store(name="B")
    variant_a = make_variant(store_a)
    wh_a = make_warehouse(store_a)
    store_client(owner_a, store_a).post(
        RECEIVE,
        {"variant_id": str(variant_a.id), "warehouse_id": str(wh_a.id), "quantity": 7},
        format="json",
    )
    # Store B sees no stock.
    resp_b = store_client(owner_b, store_b).get(STOCK_LIST)
    assert resp_b.json()["meta"]["pagination"]["count"] == 0


def test_cannot_receive_other_stores_variant(
    store_client, make_store, make_variant, make_warehouse
):
    store_a, _owner_a = make_store(name="A")
    store_b, owner_b = make_store(name="B")
    variant_a = make_variant(store_a)
    wh_b = make_warehouse(store_b)
    resp = store_client(owner_b, store_b).post(
        RECEIVE,
        {"variant_id": str(variant_a.id), "warehouse_id": str(wh_b.id), "quantity": 5},
        format="json",
    )
    assert resp.status_code == 400
    assert "variant_id" in resp.json()["errors"]


def test_low_stock_report(store_client, make_store, make_variant, make_warehouse):
    store, owner = make_store()
    variant = make_variant(store)
    warehouse = make_warehouse(store)
    client = store_client(owner, store)
    client.post(
        RECEIVE,
        {"variant_id": str(variant.id), "warehouse_id": str(warehouse.id), "quantity": 5},
        format="json",
    )
    # Raise the reorder point above available -> item becomes low stock.
    StockItem.objects.filter(variant=variant, warehouse=warehouse).update(reorder_point=10)
    resp = client.get(LOW_STOCK)
    assert resp.status_code == 200
    assert resp.json()["meta"]["pagination"]["count"] == 1
