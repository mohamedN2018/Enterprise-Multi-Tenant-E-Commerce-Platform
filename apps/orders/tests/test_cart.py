"""Cart management tests."""

from __future__ import annotations

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db

CART = reverse("v1:cart:cart")
ADD = reverse("v1:cart:item-add")


def _item_url(item_id):
    return reverse("v1:cart:item-detail", kwargs={"item_id": item_id})


def test_add_item_to_cart(store_client, make_store, make_user, make_variant, seed_stock):
    store = make_store()
    variant = make_variant(store, price="12.50")
    seed_stock(store, variant, 10)
    buyer = make_user()
    client = store_client(buyer, store)

    resp = client.post(ADD, {"variant_id": str(variant.id), "quantity": 2}, format="json")
    assert resp.status_code == 201
    assert resp.json()["data"]["quantity"] == 2

    cart = client.get(CART).json()["data"]
    assert cart["item_count"] == 2
    assert cart["subtotal"] == "25.00"


def test_adding_same_variant_merges(store_client, make_store, make_user, make_variant, seed_stock):
    store = make_store()
    variant = make_variant(store)
    seed_stock(store, variant, 10)
    client = store_client(make_user(), store)
    client.post(ADD, {"variant_id": str(variant.id), "quantity": 2}, format="json")
    client.post(ADD, {"variant_id": str(variant.id), "quantity": 3}, format="json")
    assert client.get(CART).json()["data"]["item_count"] == 5


def test_cannot_add_more_than_available(
    store_client, make_store, make_user, make_variant, seed_stock
):
    store = make_store()
    variant = make_variant(store)
    seed_stock(store, variant, 3)
    client = store_client(make_user(), store)
    resp = client.post(ADD, {"variant_id": str(variant.id), "quantity": 5}, format="json")
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "insufficient_stock"


def test_cannot_add_unpublished_product(
    store_client, make_store, make_user, make_variant, seed_stock
):
    store = make_store()
    variant = make_variant(store, published=False)
    seed_stock(store, variant, 10)
    client = store_client(make_user(), store)
    resp = client.post(ADD, {"variant_id": str(variant.id), "quantity": 1}, format="json")
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "not_purchasable"


def test_update_and_remove_item(store_client, make_store, make_user, make_variant, seed_stock):
    store = make_store()
    variant = make_variant(store)
    seed_stock(store, variant, 10)
    client = store_client(make_user(), store)
    item_id = client.post(
        ADD, {"variant_id": str(variant.id), "quantity": 2}, format="json"
    ).json()["data"]["id"]

    # Update quantity.
    resp = client.patch(_item_url(item_id), {"quantity": 4}, format="json")
    assert resp.status_code == 200
    assert client.get(CART).json()["data"]["item_count"] == 4

    # Quantity 0 removes the item.
    resp = client.patch(_item_url(item_id), {"quantity": 0}, format="json")
    assert resp.status_code == 200
    assert client.get(CART).json()["data"]["item_count"] == 0


def test_clear_cart(store_client, make_store, make_user, make_variant, seed_stock):
    store = make_store()
    variant = make_variant(store)
    seed_stock(store, variant, 10)
    client = store_client(make_user(), store)
    client.post(ADD, {"variant_id": str(variant.id), "quantity": 2}, format="json")
    assert client.delete(CART).status_code == 200
    assert client.get(CART).json()["data"]["item_count"] == 0


def test_cart_requires_store_context(make_user):
    from rest_framework.test import APIClient

    client = APIClient()
    client.force_authenticate(user=make_user())
    assert client.get(CART).status_code == 400
