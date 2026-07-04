"""Product variant tests: default handling + SKU uniqueness."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.catalog.services import CatalogService

pytestmark = pytest.mark.django_db

PRODUCT_LIST = reverse("v1:catalog:product-list")


def _make_product(store):
    return CatalogService().create_product(store=store, data={"name": "Tee"})


def _variants_url(product_id):
    return reverse("v1:catalog:variant-list", kwargs={"product_id": product_id})


def test_first_variant_is_default(store_client, make_store):
    store, owner = make_store()
    product = _make_product(store)
    resp = store_client(owner, store).post(
        _variants_url(product.id), {"sku": "TEE-001", "price": "19.99"}, format="json"
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["is_default"] is True


def test_negative_price_rejected(store_client, make_store):
    """A negative price would flow into carts/orders/payouts as a credit."""
    store, owner = make_store()
    product = _make_product(store)
    resp = store_client(owner, store).post(
        _variants_url(product.id), {"sku": "NEG-1", "price": "-5.00"}, format="json"
    )
    assert resp.status_code == 400


def test_second_variant_not_default_unless_requested(store_client, make_store):
    store, owner = make_store()
    product = _make_product(store)
    client = store_client(owner, store)
    url = _variants_url(product.id)
    client.post(url, {"sku": "A", "price": "10.00"}, format="json")
    second = client.post(url, {"sku": "B", "price": "12.00"}, format="json")
    assert second.status_code == 201
    assert second.json()["data"]["is_default"] is False


def test_setting_default_clears_previous(store_client, make_store):
    store, owner = make_store()
    product = _make_product(store)
    client = store_client(owner, store)
    url = _variants_url(product.id)
    first = client.post(url, {"sku": "A", "price": "10.00"}, format="json").json()["data"]
    second = client.post(
        url, {"sku": "B", "price": "12.00", "is_default": True}, format="json"
    ).json()["data"]

    assert second["is_default"] is True
    first_detail = reverse(
        "v1:catalog:variant-detail",
        kwargs={"product_id": product.id, "variant_id": first["id"]},
    )
    assert client.get(first_detail).json()["data"]["is_default"] is False


def test_duplicate_sku_conflict(store_client, make_store):
    store, owner = make_store()
    product = _make_product(store)
    client = store_client(owner, store)
    url = _variants_url(product.id)
    client.post(url, {"sku": "DUP", "price": "10.00"}, format="json")
    dupe = client.post(url, {"sku": "DUP", "price": "11.00"}, format="json")
    assert dupe.status_code == 409
    assert dupe.json()["error_code"] == "sku_taken"


def test_variant_creation_requires_write_role(store_client, make_store, make_user, add_member):
    from apps.stores.models import StoreRole

    store, _owner = make_store()
    employee = make_user()
    add_member(store, employee, StoreRole.EMPLOYEE)
    product = _make_product(store)
    resp = store_client(employee, store).post(
        _variants_url(product.id), {"sku": "X", "price": "9.99"}, format="json"
    )
    assert resp.status_code == 403
