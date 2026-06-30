"""Store CRUD + RBAC tests."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.stores.models import Store, StoreMembership, StoreRole, StoreSettings

pytestmark = pytest.mark.django_db

LIST_URL = reverse("v1:stores:store-list")


def _detail(store_id):
    return reverse("v1:stores:store-detail", kwargs={"store_id": store_id})


def test_create_store_makes_owner_membership_and_settings(client_for, make_user):
    user = make_user()
    client = client_for(user)
    resp = client.post(LIST_URL, {"name": "My Shop"}, format="json")
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["slug"] == "my-shop"
    assert data["owner"] == str(user.id)

    store = Store.objects.get(id=data["id"])
    assert StoreSettings.objects.filter(store=store).exists()
    membership = StoreMembership.objects.get(store=store, user=user)
    assert membership.role == StoreRole.OWNER


def test_create_store_generates_unique_slug(client_for, make_user, make_store):
    make_store(name="Repeat")  # first "repeat"
    user = make_user()
    client = client_for(user)
    resp = client.post(LIST_URL, {"name": "Repeat"}, format="json")
    assert resp.status_code == 201
    assert resp.json()["data"]["slug"] == "repeat-2"


def test_list_returns_only_my_stores(client_for, make_store, make_user):
    store, owner = make_store()
    make_store()  # someone else's store
    client = client_for(owner)
    resp = client.get(LIST_URL)
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["pagination"]["count"] == 1
    assert body["data"][0]["id"] == str(store.id)


def test_retrieve_requires_membership(client_for, make_store, make_user):
    store, _owner = make_store()
    outsider = make_user()
    resp = client_for(outsider).get(_detail(store.id))
    assert resp.status_code == 403


def test_owner_can_update_store(client_for, make_store):
    store, owner = make_store()
    resp = client_for(owner).patch(
        _detail(store.id), {"description": "Now with stuff", "status": "active"}, format="json"
    )
    assert resp.status_code == 200
    store.refresh_from_db()
    assert store.description == "Now with stuff"
    assert store.status == "active"


def test_employee_cannot_update_store(client_for, make_store, make_user):
    store, _owner = make_store()
    employee = make_user()
    StoreMembership.objects.create(
        store=store, user=employee, role=StoreRole.EMPLOYEE, is_active=True
    )
    resp = client_for(employee).patch(_detail(store.id), {"description": "hacked"}, format="json")
    assert resp.status_code == 403


def test_only_owner_can_delete_store(client_for, make_store, make_user):
    store, _owner = make_store()
    manager = make_user()
    StoreMembership.objects.create(
        store=store, user=manager, role=StoreRole.MANAGER, is_active=True
    )
    # Manager forbidden
    assert client_for(manager).delete(_detail(store.id)).status_code == 403


def test_owner_delete_soft_deletes(client_for, make_store):
    store, owner = make_store()
    resp = client_for(owner).delete(_detail(store.id))
    assert resp.status_code == 200
    assert not Store.objects.filter(id=store.id).exists()
    assert Store.all_objects.filter(id=store.id, is_deleted=True).exists()


def test_settings_get_and_update(client_for, make_store):
    store, owner = make_store()
    url = reverse("v1:stores:store-settings", kwargs={"store_id": store.id})
    client = client_for(owner)
    assert client.get(url).status_code == 200
    resp = client.patch(url, {"default_tax_rate": "15.00", "track_inventory": False}, format="json")
    assert resp.status_code == 200
    store.settings.refresh_from_db()
    assert str(store.settings.default_tax_rate) == "15.00"
    assert store.settings.track_inventory is False
