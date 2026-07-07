"""Cashier (POS) integration: key management, in-store sale deduction, pull, sync."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.inventory.models import StockItem
from apps.inventory.services import InventoryService
from apps.stores.models import StoreRole

pytestmark = pytest.mark.django_db

CONNECTION_URL = reverse("v1:pos:connection")
ROTATE_URL = reverse("v1:pos:connection-rotate")
SALES_URL = reverse("v1:pos:sales")
STOCK_URL = reverse("v1:pos:stock")


def _link(store_client, store, owner, **body):
    """Create the connection and return the plaintext API key."""
    resp = store_client(owner, store).post(CONNECTION_URL, body, format="json")
    assert resp.status_code == 201, resp.content
    return resp.json()["data"]["api_key"]


def _on_hand(store, variant):
    return sum(
        i.quantity for i in StockItem.all_objects.filter(store=store, variant=variant)
    )


# --- Management ------------------------------------------------------------
def test_owner_links_cashier_and_key_shown_once(store_client, make_store):
    store, owner = make_store()
    key = _link(store_client, store, owner, name="Front Till")
    assert key.startswith("pos_")

    # A later GET never re-reveals the key, only its masked prefix.
    data = store_client(owner, store).get(CONNECTION_URL).json()["data"]
    assert data["name"] == "Front Till"
    assert "api_key" not in data
    assert data["masked_key"].endswith("…")


def test_one_connection_per_store(store_client, make_store):
    store, owner = make_store()
    _link(store_client, store, owner)
    dup = store_client(owner, store).post(CONNECTION_URL, {}, format="json")
    assert dup.status_code == 409
    assert dup.json()["error_code"] == "pos_already_linked"


def test_employee_without_settings_cannot_link(store_client, make_store, make_user, add_member):
    store, owner = make_store()
    employee = make_user()
    add_member(store, employee, StoreRole.EMPLOYEE, permissions=["catalog"])
    resp = store_client(employee, store).post(CONNECTION_URL, {}, format="json")
    assert resp.status_code == 403


def test_employee_with_settings_can_link(store_client, make_store, make_user, add_member):
    store, owner = make_store()
    employee = make_user()
    add_member(store, employee, StoreRole.EMPLOYEE, permissions=["settings"])
    resp = store_client(employee, store).post(CONNECTION_URL, {}, format="json")
    assert resp.status_code == 201


def test_unlink(store_client, make_store):
    store, owner = make_store()
    _link(store_client, store, owner)
    assert store_client(owner, store).delete(CONNECTION_URL).status_code == 200
    assert store_client(owner, store).get(CONNECTION_URL).json()["data"] is None


# --- Cashier auth ----------------------------------------------------------
def test_missing_or_bad_key_rejected(store_client, make_store):
    store, owner = make_store()
    _link(store_client, store, owner)
    assert APIClient().get(STOCK_URL).status_code == 401
    assert APIClient().get(STOCK_URL, HTTP_X_POS_KEY="pos_wrong").status_code == 401


# --- Inbound: sale deducts warehouse stock ---------------------------------
def test_cashier_sale_deducts_stock(store_client, make_store, make_variant):
    store, owner = make_store()
    _product, variant = make_variant(store, sku="TSHIRT-1", stock=10)
    key = _link(store_client, store, owner)

    resp = APIClient().post(
        SALES_URL,
        {"items": [{"sku": "TSHIRT-1", "quantity": 3}], "reference": "receipt-42"},
        format="json",
        HTTP_X_POS_KEY=key,
    )
    assert resp.status_code == 200, resp.content
    assert _on_hand(store, variant) == 7
    item = resp.json()["data"]["items"][0]
    assert item["sku"] == "TSHIRT-1" and item["on_hand"] == 7


def test_unknown_sku_rejected(store_client, make_store, make_variant):
    store, owner = make_store()
    make_variant(store, sku="KNOWN-1", stock=5)
    key = _link(store_client, store, owner)
    resp = APIClient().post(
        SALES_URL, {"items": [{"sku": "NOPE", "quantity": 1}]}, format="json", HTTP_X_POS_KEY=key
    )
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "unknown_sku"


def test_oversell_rejected_and_atomic(store_client, make_store, make_variant):
    store, owner = make_store()
    _p1, v1 = make_variant(store, sku="A-1", stock=5)
    _p2, v2 = make_variant(store, sku="B-1", stock=5)
    key = _link(store_client, store, owner)

    # First line is fine, second oversells — the whole sale must roll back.
    resp = APIClient().post(
        SALES_URL,
        {"items": [{"sku": "A-1", "quantity": 2}, {"sku": "B-1", "quantity": 99}]},
        format="json",
        HTTP_X_POS_KEY=key,
    )
    assert resp.status_code == 422
    assert _on_hand(store, v1) == 5  # unchanged
    assert _on_hand(store, v2) == 5


# --- Pull: current levels --------------------------------------------------
def test_stock_pull_snapshot(store_client, make_store, make_variant):
    store, owner = make_store()
    make_variant(store, sku="P-1", stock=4)
    key = _link(store_client, store, owner)
    data = APIClient().get(STOCK_URL, {"sku": "P-1"}, HTTP_X_POS_KEY=key).json()["data"]
    item = data["items"][0]
    assert item["sku"] == "P-1" and item["available"] == 4 and item["in_stock"] is True


# --- Rotation --------------------------------------------------------------
def test_rotate_invalidates_old_key(store_client, make_store):
    store, owner = make_store()
    old = _link(store_client, store, owner)
    new = store_client(owner, store).post(ROTATE_URL, {}, format="json").json()["data"]["api_key"]

    assert old != new
    assert APIClient().get(STOCK_URL, HTTP_X_POS_KEY=old).status_code == 401
    assert APIClient().get(STOCK_URL, HTTP_X_POS_KEY=new).status_code == 200


# --- Outbound sync (platform -> cashier) -----------------------------------
def test_online_sale_pushes_to_webhook(
    store_client, make_store, make_variant, monkeypatch, django_capture_on_commit_callbacks
):
    store, owner = make_store()
    _product, variant = make_variant(store, sku="W-1", stock=10)
    _link(store_client, store, owner)
    store_client(owner, store).patch(
        CONNECTION_URL, {"webhook_url": "https://cashier.example/hook"}, format="json"
    )

    calls = []
    monkeypatch.setattr(
        "apps.pos.tasks.push_stock_update.delay", lambda *a, **k: calls.append(a)
    )
    warehouse = InventoryService.default_warehouse(store=store)

    with django_capture_on_commit_callbacks(execute=True):
        # An online sale / issue (NOT tagged pos-sale) must notify the cashier.
        InventoryService().issue(
            store=store, variant=variant, warehouse=warehouse, quantity=1, reference="order-9"
        )

    assert calls and calls[0][1] == "W-1"


def test_cashier_sale_does_not_echo_to_webhook(
    store_client, make_store, make_variant, monkeypatch, django_capture_on_commit_callbacks
):
    store, owner = make_store()
    make_variant(store, sku="E-1", stock=10)
    key = _link(store_client, store, owner)
    store_client(owner, store).patch(
        CONNECTION_URL, {"webhook_url": "https://cashier.example/hook"}, format="json"
    )

    calls = []
    monkeypatch.setattr(
        "apps.pos.tasks.push_stock_update.delay", lambda *a, **k: calls.append(a)
    )

    with django_capture_on_commit_callbacks(execute=True):
        APIClient().post(
            SALES_URL, {"items": [{"sku": "E-1", "quantity": 1}]}, format="json", HTTP_X_POS_KEY=key
        )

    assert calls == []  # POS-originated deduction is not echoed back
