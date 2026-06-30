"""Warehouse CRUD + RBAC tests."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.inventory.models import Warehouse
from apps.stores.models import StoreRole

pytestmark = pytest.mark.django_db

WAREHOUSE_LIST = reverse("v1:inventory:warehouse-list")


def test_create_warehouse(store_client, make_store):
    store, owner = make_store()
    resp = store_client(owner, store).post(
        WAREHOUSE_LIST, {"name": "Main", "code": "MAIN"}, format="json"
    )
    assert resp.status_code == 201
    assert Warehouse.objects.filter(store=store, code="MAIN").exists()


def test_duplicate_code_conflict(store_client, make_store):
    store, owner = make_store()
    client = store_client(owner, store)
    client.post(WAREHOUSE_LIST, {"name": "A", "code": "DUP"}, format="json")
    dupe = client.post(WAREHOUSE_LIST, {"name": "B", "code": "DUP"}, format="json")
    assert dupe.status_code == 409
    assert dupe.json()["error_code"] == "code_taken"


def test_single_default_enforced(store_client, make_store, make_warehouse):
    store, owner = make_store()
    first = make_warehouse(store, code="W1", is_default=True)
    resp = store_client(owner, store).post(
        WAREHOUSE_LIST, {"name": "Second", "code": "W2", "is_default": True}, format="json"
    )
    assert resp.status_code == 201
    first.refresh_from_db()
    assert first.is_default is False


def test_employee_cannot_create_warehouse(store_client, make_store, make_user, add_member):
    store, _owner = make_store()
    employee = make_user()
    add_member(store, employee, StoreRole.EMPLOYEE)
    resp = store_client(employee, store).post(
        WAREHOUSE_LIST, {"name": "X", "code": "X"}, format="json"
    )
    assert resp.status_code == 403
