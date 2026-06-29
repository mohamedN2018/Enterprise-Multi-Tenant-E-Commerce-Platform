"""Referral system tests (P2.6b): codes, apply guards, reward-on-confirm, stats."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.rewards.models import Referral, ReferralCode
from apps.rewards.services import WalletService

pytestmark = pytest.mark.django_db

CODE = reverse("v1:rewards:referral-code")
APPLY = reverse("v1:rewards:referral-apply")
LIST = reverse("v1:rewards:referral-list")


def _get_code(client) -> str:
    return client.get(CODE).json()["data"]["code"]


def _place_and_confirm(client, variant, qty=1):
    client.post(
        reverse("v1:cart:item-add"),
        {"variant_id": str(variant.id), "quantity": qty},
        format="json",
    )
    order = client.post(reverse("v1:cart:checkout"), {}, format="json").json()["data"]
    client.post(reverse("v1:orders:confirm", kwargs={"order_id": order["id"]}))
    return order


def _enable_rewards(settings, *, referrer="10.00", referee="5.00", min_order="0.00"):
    settings.REWARDS = {
        **settings.REWARDS,
        "REFERRER_REWARD": referrer,
        "REFEREE_REWARD": referee,
        "REFERRAL_MIN_ORDER": min_order,
    }


def test_referral_code_is_stable_and_stats_start_empty(make_store, make_user, store_client):
    store, _ = make_store()
    client = store_client(make_user(), store)
    data = client.get(CODE).json()["data"]
    assert data["code"]
    assert data["total_referrals"] == 0
    assert data["pending"] == 0
    assert client.get(CODE).json()["data"]["code"] == data["code"]  # same code on re-fetch


def test_apply_code_creates_pending_referral(make_store, make_user, store_client):
    store, _ = make_store()
    code = _get_code(store_client(make_user(), store))
    resp = store_client(make_user(), store).post(APPLY, {"code": code}, format="json")
    assert resp.status_code == 201
    assert resp.json()["data"]["status"] == "pending"


def test_cannot_use_own_code(make_store, make_user, store_client):
    store, _ = make_store()
    referrer = make_user()
    client = store_client(referrer, store)
    code = _get_code(client)
    resp = client.post(APPLY, {"code": code}, format="json")
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "self_referral"


def test_invalid_code_rejected(make_store, make_user, store_client):
    store, _ = make_store()
    resp = store_client(make_user(), store).post(APPLY, {"code": "NOPE1234"}, format="json")
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "invalid_referral_code"


def test_cannot_be_referred_twice(make_store, make_user, store_client):
    store, _ = make_store()
    code_a = _get_code(store_client(make_user(), store))
    code_b = _get_code(store_client(make_user(), store))
    referee = store_client(make_user(), store)
    assert referee.post(APPLY, {"code": code_a}, format="json").status_code == 201
    dup = referee.post(APPLY, {"code": code_b}, format="json")
    assert dup.status_code == 409
    assert dup.json()["error_code"] == "already_referred"


def test_existing_customer_cannot_apply(make_store, make_user, store_client, make_variant):
    store, _ = make_store()
    code = _get_code(store_client(make_user(), store))
    referee = make_user()
    referee_client = store_client(referee, store)
    _place_and_confirm(referee_client, make_variant(store))  # referee already shopped
    resp = referee_client.post(APPLY, {"code": code}, format="json")
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "existing_customer"


def test_reward_paid_on_qualifying_order(
    make_store, make_user, store_client, make_variant, settings
):
    _enable_rewards(settings, referrer="10.00", referee="5.00", min_order="0.00")
    store, _ = make_store()
    referrer = make_user()
    referee = make_user()
    code = _get_code(store_client(referrer, store))
    referee_client = store_client(referee, store)
    referee_client.post(APPLY, {"code": code}, format="json")
    _place_and_confirm(referee_client, make_variant(store, price="60.00"))

    assert WalletService().balance(store=store, user=referrer) == Decimal("10.00")
    assert WalletService().balance(store=store, user=referee) == Decimal("5.00")
    made = store_client(referrer, store).get(LIST).json()["data"]
    assert made[0]["status"] == "rewarded"
    code_row = ReferralCode.objects.get(store=store, user=referrer)
    assert code_row.uses_count == 1


def test_below_min_order_stays_pending(make_store, make_user, store_client, make_variant, settings):
    _enable_rewards(settings, referrer="10.00", referee="5.00", min_order="100.00")
    store, _ = make_store()
    referrer = make_user()
    referee = make_user()
    code = _get_code(store_client(referrer, store))
    referee_client = store_client(referee, store)
    referee_client.post(APPLY, {"code": code}, format="json")
    _place_and_confirm(referee_client, make_variant(store, price="60.00"))  # 60 < 100

    assert WalletService().balance(store=store, user=referrer) == Decimal("0.00")
    referral = Referral.objects.get(store=store, referee=referee)
    assert referral.status == "pending"


def test_no_referral_is_a_noop_on_confirm(make_store, make_user, store_client, make_variant):
    store, _ = make_store()
    client = store_client(make_user(), store)
    _place_and_confirm(client, make_variant(store))  # buyer never used a referral
    assert Referral.objects.count() == 0


def test_referral_codes_are_store_scoped(make_store, make_user, store_client):
    store_a, _ = make_store(name="A")
    store_b, _ = make_store(name="B")
    user = make_user()
    _get_code(store_client(user, store_a))
    _get_code(store_client(user, store_b))
    assert ReferralCode.objects.filter(store=store_a, user=user).count() == 1
    assert ReferralCode.objects.filter(store=store_b, user=user).count() == 1
