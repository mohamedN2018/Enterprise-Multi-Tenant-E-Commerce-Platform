"""Granular employee permissions: an employee writes only granted areas."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.stores.models import StoreMembership, StoreRole

pytestmark = pytest.mark.django_db

PRODUCT_LIST = reverse("v1:catalog:product-list")


def _employee(store, make_user, permissions):
    user = make_user()
    StoreMembership.objects.create(
        store=store, user=user, role=StoreRole.EMPLOYEE, permissions=permissions, is_active=True
    )
    return user


def test_employee_without_area_cannot_write(store_client, make_store, make_user):
    store, _owner = make_store()
    emp = _employee(store, make_user, [])
    resp = store_client(emp, store).post(PRODUCT_LIST, {"name": "X"}, format="json")
    assert resp.status_code == 403


def test_employee_with_catalog_permission_can_write(store_client, make_store, make_user):
    store, _owner = make_store()
    emp = _employee(store, make_user, ["catalog"])
    resp = store_client(emp, store).post(PRODUCT_LIST, {"name": "X"}, format="json")
    assert resp.status_code == 201


def test_employee_permission_is_area_scoped(store_client, make_store, make_user):
    # 'sales' does not grant catalog writes.
    store, _owner = make_store()
    emp = _employee(store, make_user, ["sales"])
    resp = store_client(emp, store).post(PRODUCT_LIST, {"name": "X"}, format="json")
    assert resp.status_code == 403


def test_employee_can_always_read(store_client, make_store, make_user):
    store, _owner = make_store()
    emp = _employee(store, make_user, [])
    assert store_client(emp, store).get(PRODUCT_LIST).status_code == 200


def test_manager_writes_without_needing_permissions(store_client, make_store, make_user):
    store, _owner = make_store()
    mgr = make_user()
    StoreMembership.objects.create(
        store=store, user=mgr, role=StoreRole.MANAGER, permissions=[], is_active=True
    )
    resp = store_client(mgr, store).post(PRODUCT_LIST, {"name": "X"}, format="json")
    assert resp.status_code == 201
