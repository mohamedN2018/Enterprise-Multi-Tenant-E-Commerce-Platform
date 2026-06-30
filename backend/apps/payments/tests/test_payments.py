"""Payment flow tests: gateways, capture -> order confirm -> stock commit."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.inventory.models import StockItem
from apps.orders.models import OrderStatus
from apps.payments.models import PaymentStatus

pytestmark = pytest.mark.django_db

GATEWAYS = reverse("v1:payments:gateways")
PAYMENTS = reverse("v1:payments:list")


def _create_payment(client, order_id, gateway="manual"):
    return client.post(PAYMENTS, {"order_id": order_id, "gateway": gateway}, format="json")


def test_list_enabled_gateways(make_store, place_order):
    store = make_store()
    client, *_ = place_order(store)
    resp = client.get(GATEWAYS)
    assert resp.status_code == 200
    codes = {g["code"] for g in resp.json()["data"]}
    assert "manual" in codes
    assert "stripe" in codes  # enabled (stub) in test settings


def test_create_payment_initiates(make_store, place_order):
    store = make_store()
    client, _buyer, _variant, order = place_order(store)
    resp = _create_payment(client, order["id"])
    assert resp.status_code == 201
    assert resp.json()["data"]["status"] == PaymentStatus.PROCESSING


def test_capture_confirms_order_and_commits_stock(make_store, place_order):
    store = make_store()
    client, _buyer, variant, order = place_order(store, qty=3, stock=10)
    payment = _create_payment(client, order["id"]).json()["data"]

    capture = client.post(reverse("v1:payments:capture", kwargs={"payment_id": payment["id"]}))
    assert capture.status_code == 200
    assert capture.json()["data"]["status"] == PaymentStatus.CAPTURED

    # Order is confirmed and the reserved stock is now deducted.
    order_detail = client.get(reverse("v1:orders:detail", kwargs={"order_id": order["id"]}))
    assert order_detail.json()["data"]["status"] == OrderStatus.CONFIRMED
    item = StockItem.objects.get(variant=variant)
    assert item.quantity == 7
    assert item.reserved_quantity == 0


def test_cannot_pay_a_confirmed_order(make_store, place_order):
    store = make_store()
    client, _buyer, _variant, order = place_order(store)
    payment = _create_payment(client, order["id"]).json()["data"]
    client.post(reverse("v1:payments:capture", kwargs={"payment_id": payment["id"]}))

    # Order is now confirmed; a new payment cannot be created.
    resp = _create_payment(client, order["id"])
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "order_not_payable"


def test_stripe_stub_reports_unconfigured(make_store, place_order):
    store = make_store()
    client, _buyer, _variant, order = place_order(store)
    resp = _create_payment(client, order["id"], gateway="stripe")
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "gateway_unconfigured"


def test_unknown_gateway_rejected(make_store, place_order):
    store = make_store()
    client, _buyer, _variant, order = place_order(store)
    resp = _create_payment(client, order["id"], gateway="bitcoin")
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "gateway_unavailable"


def test_payments_scoped_to_buyer(make_store, place_order, store_client, make_user):
    store = make_store()
    client, _buyer, _variant, order = place_order(store)
    _create_payment(client, order["id"])

    other = make_user()
    resp = store_client(other, store).get(PAYMENTS)
    assert resp.json()["meta"]["pagination"]["count"] == 0
