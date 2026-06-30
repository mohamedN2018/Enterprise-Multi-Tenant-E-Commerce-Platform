"""Seller payout & commission tests (E4)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.orders.models import Order
from apps.payouts.models import SellerAccount
from apps.payouts.services import PayoutService
from apps.stores.models import StoreRole

from .conftest import place_and_confirm

pytestmark = pytest.mark.django_db

ACCOUNT = reverse("v1:payouts:account")
COMMISSION = reverse("v1:payouts:commission")
LEDGER = reverse("v1:payouts:ledger")
PAYOUTS = reverse("v1:payouts:list")


def test_earning_credited_on_confirm(make_store, make_user, make_variant, store_client):
    store, owner = make_store()
    variant = make_variant(store, price="50.00")
    place_and_confirm(store_client(make_user(), store), variant, qty=2)  # total 100
    account = store_client(owner, store).get(ACCOUNT).json()["data"]
    assert account["balance"] == "100.00"
    assert account["commission_rate"] == "0.00"


def test_commission_is_deducted(make_store, make_user, make_variant, store_client):
    store, owner = make_store()
    owner_client = store_client(owner, store)
    owner_client.put(COMMISSION, {"rate": "10"}, format="json")  # 10% platform cut
    variant = make_variant(store, price="50.00")
    place_and_confirm(store_client(make_user(), store), variant, qty=2)  # gross 100

    assert owner_client.get(ACCOUNT).json()["data"]["balance"] == "90.00"
    earning = next(
        e for e in owner_client.get(LEDGER).json()["data"] if e["entry_type"] == "earning"
    )
    assert earning["commission_amount"] == "10.00"
    assert earning["net_amount"] == "90.00"


def test_request_payout_debits_balance(make_store, make_user, make_variant, store_client):
    store, owner = make_store()
    place_and_confirm(store_client(make_user(), store), make_variant(store, price="50.00"), qty=2)
    owner_client = store_client(owner, store)
    resp = owner_client.post(PAYOUTS, {"amount": "60"}, format="json")
    assert resp.status_code == 201
    assert resp.json()["data"]["status"] == "pending"
    assert owner_client.get(ACCOUNT).json()["data"]["balance"] == "40.00"


def test_payout_insufficient_balance(make_store, make_user, store_client):
    store, owner = make_store()
    resp = store_client(owner, store).post(PAYOUTS, {"amount": "100"}, format="json")
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "insufficient_balance"


def test_mark_payout_paid(make_store, make_user, make_variant, store_client):
    store, owner = make_store()
    place_and_confirm(store_client(make_user(), store), make_variant(store, price="50.00"), qty=2)
    owner_client = store_client(owner, store)
    payout = owner_client.post(PAYOUTS, {"amount": "50"}, format="json").json()["data"]
    resp = owner_client.post(reverse("v1:payouts:mark-paid", kwargs={"payout_id": payout["id"]}))
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "paid"


def test_earning_is_idempotent(make_store, make_user, make_variant, store_client):
    store, _owner = make_store()
    order_data = place_and_confirm(
        store_client(make_user(), store), make_variant(store, price="50.00"), qty=2
    )
    order = Order.objects.get(id=order_data["id"])
    assert PayoutService().record_order_earning(order=order) is None  # already recorded
    assert PayoutService().balance(store=store) == Decimal("100.00")


def test_set_commission_requires_write(make_store, make_user, add_member, store_client):
    store, owner = make_store()
    employee = make_user()
    add_member(store, employee, StoreRole.EMPLOYEE)
    assert (
        store_client(employee, store).put(COMMISSION, {"rate": "5"}, format="json").status_code
        == 403
    )
    assert (
        store_client(owner, store).put(COMMISSION, {"rate": "5"}, format="json").status_code == 200
    )


def test_accounts_are_store_scoped(make_store):
    store_a, _owner_a = make_store(name="A")
    store_b, _owner_b = make_store(name="B")
    PayoutService().get_account(store=store_a)
    assert SellerAccount.objects.filter(store=store_a).count() == 1
    assert SellerAccount.objects.filter(store=store_b).count() == 0
