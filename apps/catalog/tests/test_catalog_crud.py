"""Catalog CRUD, store-context, and RBAC tests."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.catalog.models import Category, Product, ProductStatus
from apps.stores.models import StoreRole

pytestmark = pytest.mark.django_db

CATEGORY_LIST = reverse("v1:catalog:category-list")
BRAND_LIST = reverse("v1:catalog:brand-list")
PRODUCT_LIST = reverse("v1:catalog:product-list")


def test_create_category_scoped_and_slugged(store_client, make_store):
    store, owner = make_store()
    client = store_client(owner, store)
    resp = client.post(CATEGORY_LIST, {"name": "Running Shoes"}, format="json")
    assert resp.status_code == 201
    assert resp.json()["data"]["slug"] == "running-shoes"
    assert Category.objects.filter(store=store, name="Running Shoes").count() == 1


def test_slug_uniqueness_per_store(store_client, make_store):
    store, owner = make_store()
    client = store_client(owner, store)
    client.post(CATEGORY_LIST, {"name": "Sale"}, format="json")
    resp = client.post(CATEGORY_LIST, {"name": "Sale"}, format="json")
    assert resp.status_code == 201
    assert resp.json()["data"]["slug"] == "sale-2"


def test_store_context_required(make_store):
    _store, owner = make_store()
    client = APIClient()
    client.force_authenticate(user=owner)  # no X-Store-Id header
    resp = client.get(CATEGORY_LIST)
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "store_context_required"


def test_non_member_forbidden(store_client, make_store, make_user):
    store, _owner = make_store()
    outsider = make_user()
    resp = store_client(outsider, store).get(CATEGORY_LIST)
    assert resp.status_code == 403


def test_employee_can_read_but_not_write(store_client, make_store, make_user, add_member):
    store, _owner = make_store()
    employee = make_user()
    add_member(store, employee, StoreRole.EMPLOYEE)
    client = store_client(employee, store)
    assert client.get(CATEGORY_LIST).status_code == 200
    assert client.post(CATEGORY_LIST, {"name": "X"}, format="json").status_code == 403


def test_manager_can_write(store_client, make_store, make_user, add_member):
    store, _owner = make_store()
    manager = make_user()
    add_member(store, manager, StoreRole.MANAGER)
    resp = store_client(manager, store).post(CATEGORY_LIST, {"name": "Gadgets"}, format="json")
    assert resp.status_code == 201


def test_create_product_default_draft(store_client, make_store):
    store, owner = make_store()
    resp = store_client(owner, store).post(
        PRODUCT_LIST, {"name": "Widget", "description": "A widget"}, format="json"
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["status"] == ProductStatus.DRAFT
    assert data["published_at"] is None


def test_publishing_sets_published_at(store_client, make_store):
    store, owner = make_store()
    client = store_client(owner, store)
    created = client.post(PRODUCT_LIST, {"name": "Widget"}, format="json").json()["data"]
    url = reverse("v1:catalog:product-detail", kwargs={"product_id": created["id"]})
    resp = client.patch(url, {"status": "published"}, format="json")
    assert resp.status_code == 200
    assert resp.json()["data"]["published_at"] is not None
    assert Product.objects.get(id=created["id"]).published_at is not None


def test_create_product_with_category_and_brand(store_client, make_store):
    store, owner = make_store()
    client = store_client(owner, store)
    cat = client.post(CATEGORY_LIST, {"name": "Tools"}, format="json").json()["data"]
    brand = client.post(BRAND_LIST, {"name": "Acme"}, format="json").json()["data"]
    resp = client.post(
        PRODUCT_LIST,
        {"name": "Hammer", "category": cat["id"], "brand": brand["id"]},
        format="json",
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["category"] == cat["id"]


def test_delete_product_soft_deletes(store_client, make_store):
    store, owner = make_store()
    client = store_client(owner, store)
    created = client.post(PRODUCT_LIST, {"name": "Temp"}, format="json").json()["data"]
    url = reverse("v1:catalog:product-detail", kwargs={"product_id": created["id"]})
    assert client.delete(url).status_code == 204
    assert not Product.objects.filter(id=created["id"]).exists()
    assert Product.all_objects.filter(id=created["id"], is_deleted=True).exists()
