"""Wishlist tests (E3): add/list/remove, idempotency, move-to-cart, scoping."""

from __future__ import annotations

import uuid

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db

WISHLIST = reverse("v1:wishlist:list")
CART = reverse("v1:cart:cart")


def _add(client, variant):
    return client.post(WISHLIST, {"variant_id": str(variant.id)}, format="json")


def _move(client, item_id, quantity):
    return client.post(
        reverse("v1:wishlist:move-to-cart", kwargs={"item_id": item_id}),
        {"quantity": quantity},
        format="json",
    )


def test_add_and_list(make_store, make_user, make_variant, store_client):
    store, _owner = make_store()
    variant = make_variant(store)
    client = store_client(make_user(), store)
    assert _add(client, variant).status_code == 201
    data = client.get(WISHLIST).json()["data"]
    assert [row["variant"] for row in data] == [str(variant.id)]


def test_add_is_idempotent(make_store, make_user, make_variant, store_client):
    store, _owner = make_store()
    variant = make_variant(store)
    client = store_client(make_user(), store)
    _add(client, variant)
    _add(client, variant)
    assert len(client.get(WISHLIST).json()["data"]) == 1


def test_remove(make_store, make_user, make_variant, store_client):
    store, _owner = make_store()
    variant = make_variant(store)
    client = store_client(make_user(), store)
    item = _add(client, variant).json()["data"]
    resp = client.delete(reverse("v1:wishlist:detail", kwargs={"item_id": item["id"]}))
    assert resp.status_code == 200
    assert client.get(WISHLIST).json()["data"] == []


def test_move_to_cart(make_store, make_user, make_variant, store_client):
    store, _owner = make_store()
    variant = make_variant(store, stock=10)
    client = store_client(make_user(), store)
    item = _add(client, variant).json()["data"]
    assert _move(client, item["id"], 2).status_code == 201
    assert client.get(WISHLIST).json()["data"] == []  # moved out of the wishlist
    assert client.get(CART).json()["data"]["item_count"] == 2


def test_move_to_cart_insufficient_stock_keeps_item(
    make_store, make_user, make_variant, store_client
):
    store, _owner = make_store()
    variant = make_variant(store, stock=1)
    client = store_client(make_user(), store)
    item = _add(client, variant).json()["data"]
    assert _move(client, item["id"], 5).status_code == 422
    assert len(client.get(WISHLIST).json()["data"]) == 1  # rolled back, still wishlisted


def test_wishlist_is_user_scoped(make_store, make_user, make_variant, store_client):
    store, _owner = make_store()
    variant = make_variant(store)
    _add(store_client(make_user(), store), variant)
    assert store_client(make_user(), store).get(WISHLIST).json()["data"] == []


def test_add_invalid_variant(make_store, make_user, store_client):
    store, _owner = make_store()
    resp = store_client(make_user(), store).post(
        WISHLIST, {"variant_id": str(uuid.uuid4())}, format="json"
    )
    assert resp.status_code == 400
