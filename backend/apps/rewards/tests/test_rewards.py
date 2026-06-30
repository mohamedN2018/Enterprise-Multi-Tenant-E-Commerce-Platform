"""Rewards & wallet tests (P2.6)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.rewards.models import Wallet
from apps.rewards.services import GiftCardService, LoyaltyService, WalletService
from apps.stores.models import StoreRole

pytestmark = pytest.mark.django_db

WALLET = reverse("v1:rewards:wallet")
GIFT_REDEEM = reverse("v1:rewards:gift-card-redeem")
GIFT_CARDS = reverse("v1:rewards:gift-card-list")
LOYALTY = reverse("v1:rewards:loyalty")
LOYALTY_REDEEM = reverse("v1:rewards:loyalty-redeem")
PAYMENTS = reverse("v1:payments:list")
GATEWAYS = reverse("v1:payments:gateways")
CART_ADD = reverse("v1:cart:item-add")
CHECKOUT = reverse("v1:cart:checkout")


def _buy(client, variant, qty=1):
    client.post(CART_ADD, {"variant_id": str(variant.id), "quantity": qty}, format="json")
    return client.post(CHECKOUT).json()["data"]


# --- Wallet & gift cards ---------------------------------------------------
def test_wallet_starts_empty(store_client, make_store, make_user):
    store, _ = make_store()
    resp = store_client(make_user(), store).get(WALLET)
    assert resp.status_code == 200
    assert resp.json()["data"]["balance"] == "0.00"


def test_issue_and_redeem_gift_card(store_client, make_store, make_user):
    store, _ = make_store()
    GiftCardService().issue(store=store, amount=Decimal("50.00"), code="GC50")
    client = store_client(make_user(), store)
    resp = client.post(GIFT_REDEEM, {"code": "GC50"}, format="json")
    assert resp.status_code == 200
    assert resp.json()["data"]["wallet_balance"] == "50.00"
    # Already redeemed -> rejected.
    again = client.post(GIFT_REDEEM, {"code": "GC50"}, format="json")
    assert again.status_code == 400
    assert again.json()["error_code"] == "invalid_gift_card"


def test_gift_card_issue_requires_write(store_client, make_store, make_user, add_member):
    store, _ = make_store()
    employee = make_user()
    add_member(store, employee, StoreRole.EMPLOYEE)
    resp = store_client(employee, store).post(GIFT_CARDS, {"amount": "10.00"}, format="json")
    assert resp.status_code == 403


def test_wallets_are_store_scoped(make_store, make_user):
    store_a, _ = make_store(name="A")
    store_b, _ = make_store(name="B")
    buyer = make_user()
    WalletService().credit(store=store_a, user=buyer, amount=Decimal("5"))
    assert Wallet.objects.filter(store=store_a).count() == 1
    assert Wallet.objects.filter(store=store_b).count() == 0


# --- Loyalty ---------------------------------------------------------------
def test_loyalty_earned_on_confirm(settings, store_client, make_store, make_user, make_variant):
    settings.REWARDS = {"LOYALTY_EARN_RATE": 1, "LOYALTY_REDEEM_RATE": "0.01"}
    store, _ = make_store()
    variant = make_variant(store, price="100.00")
    client = store_client(make_user(), store)
    order = _buy(client, variant)
    client.post(reverse("v1:orders:confirm", kwargs={"order_id": order["id"]}))
    assert client.get(LOYALTY).json()["data"]["points"] == 100


def test_no_loyalty_when_rate_zero(store_client, make_store, make_user, make_variant):
    # Default earn rate is 0 -> no points, fully backward-compatible.
    store, _ = make_store()
    variant = make_variant(store, price="100.00")
    client = store_client(make_user(), store)
    order = _buy(client, variant)
    client.post(reverse("v1:orders:confirm", kwargs={"order_id": order["id"]}))
    assert client.get(LOYALTY).json()["data"]["points"] == 0


def test_loyalty_redeem_to_wallet(settings, store_client, make_store, make_user):
    settings.REWARDS = {"LOYALTY_EARN_RATE": 0, "LOYALTY_REDEEM_RATE": "0.01"}
    store, _ = make_store()
    buyer = make_user()
    LoyaltyService().earn(store=store, user=buyer, points=100, reason="seed")
    client = store_client(buyer, store)
    resp = client.post(LOYALTY_REDEEM, {"points": 100}, format="json")
    assert resp.status_code == 200
    assert resp.json()["data"]["wallet_credit"] == "1.00"
    assert client.get(WALLET).json()["data"]["balance"] == "1.00"


def test_loyalty_redeem_insufficient(store_client, make_store, make_user):
    store, _ = make_store()
    resp = store_client(make_user(), store).post(LOYALTY_REDEEM, {"points": 5}, format="json")
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "insufficient_points"


# --- Pay with store credit (wallet gateway) --------------------------------
def test_store_credit_gateway_listed(store_client, make_store, make_user, make_variant):
    store, _ = make_store()
    variant = make_variant(store)
    client = store_client(make_user(), store)
    _buy(client, variant)  # ensures store context works
    codes = {g["code"] for g in client.get(GATEWAYS).json()["data"]}
    assert "store_credit" in codes


def test_pay_with_store_credit(store_client, make_store, make_user, make_variant):
    store, _ = make_store()
    variant = make_variant(store, price="60.00", stock=10)
    buyer = make_user()
    GiftCardService().issue(store=store, amount=Decimal("100.00"), code="FUND")
    client = store_client(buyer, store)
    client.post(GIFT_REDEEM, {"code": "FUND"}, format="json")  # wallet = 100

    order = _buy(client, variant)  # total 60
    payment = client.post(
        PAYMENTS, {"order_id": order["id"], "gateway": "store_credit"}, format="json"
    ).json()["data"]
    capture = client.post(reverse("v1:payments:capture", kwargs={"payment_id": payment["id"]}))
    assert capture.status_code == 200
    assert capture.json()["data"]["status"] == "captured"
    # Wallet debited; order confirmed.
    assert client.get(WALLET).json()["data"]["balance"] == "40.00"


def test_pay_with_store_credit_insufficient(store_client, make_store, make_user, make_variant):
    store, _ = make_store()
    variant = make_variant(store, price="60.00", stock=10)
    buyer = make_user()
    GiftCardService().issue(store=store, amount=Decimal("10.00"), code="SMALL")
    client = store_client(buyer, store)
    client.post(GIFT_REDEEM, {"code": "SMALL"}, format="json")  # wallet = 10

    order = _buy(client, variant)  # total 60
    payment = client.post(
        PAYMENTS, {"order_id": order["id"], "gateway": "store_credit"}, format="json"
    ).json()["data"]
    capture = client.post(reverse("v1:payments:capture", kwargs={"payment_id": payment["id"]}))
    assert capture.status_code == 422
    assert capture.json()["error_code"] == "insufficient_funds"
    # Wallet untouched (rolled back).
    assert client.get(WALLET).json()["data"]["balance"] == "10.00"
