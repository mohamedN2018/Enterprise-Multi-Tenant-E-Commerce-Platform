"""Procurement tests (P2.2): suppliers, PO lifecycle, receiving, batches, serials."""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from django.urls import reverse

from apps.inventory.models import StockItem
from apps.procurement.models import StockBatch, Supplier
from apps.stores.models import StoreRole

pytestmark = pytest.mark.django_db

SUPPLIERS = reverse("v1:procurement:supplier-list")
POS = reverse("v1:procurement:po-list")
BATCHES = reverse("v1:procurement:batch-list")
SERIALS = reverse("v1:procurement:serial-list")


def _create_po(client, supplier, warehouse, variant, *, qty=10, unit_cost="5.00", **line_extra):
    line = {"variant_id": str(variant.id), "quantity_ordered": qty, "unit_cost": unit_cost}
    line.update(line_extra)
    return client.post(
        POS,
        {"supplier_id": str(supplier.id), "warehouse_id": str(warehouse.id), "lines": [line]},
        format="json",
    )


def _submit(client, po_id):
    return client.post(reverse("v1:procurement:po-submit", kwargs={"po_id": po_id}))


def _receive(client, po_id, body=None):
    return client.post(
        reverse("v1:procurement:po-receive", kwargs={"po_id": po_id}), body or {}, format="json"
    )


# --- Suppliers -------------------------------------------------------------
def test_supplier_create_autocodes_and_rbac(make_store, make_user, add_member, store_client):
    store, owner = make_store()
    created = store_client(owner, store).post(SUPPLIERS, {"name": "Globex"}, format="json")
    assert created.status_code == 201
    assert created.json()["data"]["code"]  # auto-generated slug
    employee = make_user()
    add_member(store, employee, StoreRole.EMPLOYEE)
    denied = store_client(employee, store).post(SUPPLIERS, {"name": "X"}, format="json")
    assert denied.status_code == 403


# --- Purchase orders -------------------------------------------------------
def test_create_purchase_order_computes_subtotal(
    make_store, store_client, make_supplier, make_warehouse, make_variant
):
    store, owner = make_store()
    client = store_client(owner, store)
    resp = _create_po(
        client,
        make_supplier(store),
        make_warehouse(store),
        make_variant(store),
        qty=10,
        unit_cost="5.00",
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["status"] == "draft"
    assert data["number"] == "PO-000001"
    assert data["subtotal"] == "50.00"


def test_submit_and_receive_updates_stock_and_batch(
    make_store, store_client, make_supplier, make_warehouse, make_variant
):
    store, owner = make_store()
    client = store_client(owner, store)
    warehouse = make_warehouse(store)
    variant = make_variant(store)
    po = _create_po(client, make_supplier(store), warehouse, variant, qty=10).json()["data"]
    assert _submit(client, po["id"]).json()["data"]["status"] == "submitted"
    received = _receive(client, po["id"]).json()["data"]
    assert received["status"] == "received"
    assert received["lines"][0]["quantity_received"] == 10

    item = StockItem.objects.get(store=store, variant=variant, warehouse=warehouse)
    assert item.quantity == 10
    batch = StockBatch.objects.get(store=store, variant=variant, warehouse=warehouse)
    assert batch.quantity == 10


def test_partial_receipt_keeps_po_submitted(
    make_store, store_client, make_supplier, make_warehouse, make_variant
):
    store, owner = make_store()
    client = store_client(owner, store)
    warehouse = make_warehouse(store)
    variant = make_variant(store)
    po = _create_po(client, make_supplier(store), warehouse, variant, qty=10).json()["data"]
    _submit(client, po["id"])
    line_id = po["lines"][0]["id"]

    partial = _receive(client, po["id"], {"lines": [{"line_id": line_id, "quantity": 4}]}).json()[
        "data"
    ]
    assert partial["status"] == "submitted"
    assert partial["lines"][0]["quantity_received"] == 4
    assert StockItem.objects.get(store=store, variant=variant, warehouse=warehouse).quantity == 4

    rest = _receive(client, po["id"], {"lines": [{"line_id": line_id, "quantity": 6}]}).json()[
        "data"
    ]
    assert rest["status"] == "received"
    assert StockItem.objects.get(store=store, variant=variant, warehouse=warehouse).quantity == 10


def test_over_receipt_is_rejected(
    make_store, store_client, make_supplier, make_warehouse, make_variant
):
    store, owner = make_store()
    client = store_client(owner, store)
    po = _create_po(
        client, make_supplier(store), make_warehouse(store), make_variant(store), qty=5
    ).json()["data"]
    _submit(client, po["id"])
    line_id = po["lines"][0]["id"]
    resp = _receive(client, po["id"], {"lines": [{"line_id": line_id, "quantity": 6}]})
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "over_receipt"


def test_cannot_receive_draft_po(
    make_store, store_client, make_supplier, make_warehouse, make_variant
):
    store, owner = make_store()
    client = store_client(owner, store)
    po = _create_po(
        client, make_supplier(store), make_warehouse(store), make_variant(store)
    ).json()["data"]
    resp = _receive(client, po["id"])  # never submitted
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "not_submitted"


def test_cannot_cancel_received_po(
    make_store, store_client, make_supplier, make_warehouse, make_variant
):
    store, owner = make_store()
    client = store_client(owner, store)
    po = _create_po(
        client, make_supplier(store), make_warehouse(store), make_variant(store)
    ).json()["data"]
    _submit(client, po["id"])
    _receive(client, po["id"])
    resp = client.post(reverse("v1:procurement:po-cancel", kwargs={"po_id": po["id"]}))
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "received"


# --- Batches / expiry ------------------------------------------------------
def test_expiry_report_filters_by_date(
    make_store, store_client, make_supplier, make_warehouse, make_variant
):
    store, owner = make_store()
    client = store_client(owner, store)
    soon = (date.today() + timedelta(days=10)).isoformat()
    po = _create_po(
        client,
        make_supplier(store),
        make_warehouse(store),
        make_variant(store),
        batch_number="LOT-A",
        expiry_date=soon,
    ).json()["data"]
    _submit(client, po["id"])
    _receive(client, po["id"])

    cutoff_after = (date.today() + timedelta(days=30)).isoformat()
    cutoff_before = (date.today() + timedelta(days=1)).isoformat()
    assert len(client.get(BATCHES, {"expiring_before": cutoff_after}).json()["data"]) == 1
    assert client.get(BATCHES, {"expiring_before": cutoff_before}).json()["data"] == []


# --- Serial numbers --------------------------------------------------------
def test_register_serials_and_update_status(make_store, store_client, make_warehouse, make_variant):
    store, owner = make_store()
    client = store_client(owner, store)
    variant = make_variant(store)
    warehouse = make_warehouse(store)
    resp = client.post(
        SERIALS,
        {
            "variant_id": str(variant.id),
            "warehouse_id": str(warehouse.id),
            "serials": ["SN1", "SN2"],
        },
        format="json",
    )
    assert resp.status_code == 201
    assert len(resp.json()["data"]) == 2
    # Duplicate is rejected.
    dup = client.post(
        SERIALS,
        {"variant_id": str(variant.id), "warehouse_id": str(warehouse.id), "serials": ["SN1"]},
        format="json",
    )
    assert dup.status_code == 409
    # Status update.
    serial_id = resp.json()["data"][0]["id"]
    patched = client.patch(
        reverse("v1:procurement:serial-detail", kwargs={"serial_id": serial_id}),
        {"status": "sold"},
        format="json",
    )
    assert patched.json()["data"]["status"] == "sold"


# --- Isolation -------------------------------------------------------------
def test_suppliers_are_store_scoped(make_store):
    store_a, _owner_a = make_store(name="A")
    store_b, _owner_b = make_store(name="B")
    Supplier.objects.create(store=store_a, name="A-only", code="a-only")
    assert Supplier.objects.filter(store=store_a).count() == 1
    assert Supplier.objects.filter(store=store_b).count() == 0
