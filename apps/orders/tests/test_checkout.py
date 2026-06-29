"""Checkout + order lifecycle tests (reserve -> confirm/cancel)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.inventory.models import StockItem
from apps.orders.models import OrderStatus

pytestmark = pytest.mark.django_db

ADD = reverse("v1:cart:item-add")
CHECKOUT = reverse("v1:cart:checkout")
ORDERS = reverse("v1:orders:list")


def _add(client, variant, qty):
    return client.post(ADD, {"variant_id": str(variant.id), "quantity": qty}, format="json")


def test_checkout_creates_order_and_reserves_stock(
    store_client, make_store, make_user, make_variant, seed_stock
):
    store = make_store()
    variant = make_variant(store, price="20.00")
    seed_stock(store, variant, 10)
    client = store_client(make_user(), store)
    _add(client, variant, 3)

    resp = client.post(CHECKOUT)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["status"] == OrderStatus.PENDING
    assert data["total"] == "60.00"
    assert len(data["items"]) == 1

    item = StockItem.objects.get(variant=variant)
    assert item.reserved_quantity == 3
    assert item.available_quantity == 7
    # The cart is now checked out (a fresh active cart would be created next time).
    assert variant.stock_items.first().reserved_quantity == 3


def test_checkout_applies_tax(store_client, make_store, make_user, make_variant, seed_stock):
    store = make_store()
    store.settings.default_tax_rate = Decimal("10")
    store.settings.save(update_fields=["default_tax_rate"])
    variant = make_variant(store, price="10.00")
    seed_stock(store, variant, 10)
    client = store_client(make_user(), store)
    _add(client, variant, 3)

    data = client.post(CHECKOUT).json()["data"]
    assert data["subtotal"] == "30.00"
    assert data["tax_total"] == "3.00"
    assert data["total"] == "33.00"


def test_checkout_empty_cart(store_client, make_store, make_user):
    store = make_store()
    client = store_client(make_user(), store)
    resp = client.post(CHECKOUT)
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "empty_cart"


def test_confirm_commits_stock(store_client, make_store, make_user, make_variant, seed_stock):
    store = make_store()
    variant = make_variant(store)
    seed_stock(store, variant, 10)
    client = store_client(make_user(), store)
    _add(client, variant, 4)
    order = client.post(CHECKOUT).json()["data"]

    url = reverse("v1:orders:confirm", kwargs={"order_id": order["id"]})
    resp = client.post(url)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == OrderStatus.CONFIRMED

    item = StockItem.objects.get(variant=variant)
    assert item.quantity == 6  # deducted
    assert item.reserved_quantity == 0


def test_cancel_releases_stock(store_client, make_store, make_user, make_variant, seed_stock):
    store = make_store()
    variant = make_variant(store)
    seed_stock(store, variant, 10)
    client = store_client(make_user(), store)
    _add(client, variant, 4)
    order = client.post(CHECKOUT).json()["data"]

    url = reverse("v1:orders:cancel", kwargs={"order_id": order["id"]})
    resp = client.post(url)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == OrderStatus.CANCELLED

    item = StockItem.objects.get(variant=variant)
    assert item.quantity == 10  # untouched
    assert item.reserved_quantity == 0  # released


def test_second_checkout_fails_when_stock_exhausted(
    store_client, make_store, make_user, make_variant, seed_stock
):
    store = make_store()
    variant = make_variant(store)
    seed_stock(store, variant, 5)
    buyer_a = store_client(make_user(), store)
    buyer_b = store_client(make_user(), store)
    # Both add 3 while 5 are available.
    _add(buyer_a, variant, 3)
    _add(buyer_b, variant, 3)
    # A checks out first -> reserves 3 (2 left).
    assert buyer_a.post(CHECKOUT).status_code == 201
    # B's checkout can no longer be fulfilled.
    resp = buyer_b.post(CHECKOUT)
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "insufficient_stock"


def test_orders_are_scoped_to_buyer_and_store(
    store_client, make_store, make_user, make_variant, seed_stock
):
    store = make_store()
    variant = make_variant(store)
    seed_stock(store, variant, 10)
    buyer = make_user()
    other = make_user()
    client = store_client(buyer, store)
    _add(client, variant, 1)
    client.post(CHECKOUT)

    # The buyer sees their order; another user sees none.
    assert store_client(buyer, store).get(ORDERS).json()["meta"]["pagination"]["count"] == 1
    assert store_client(other, store).get(ORDERS).json()["meta"]["pagination"]["count"] == 0
