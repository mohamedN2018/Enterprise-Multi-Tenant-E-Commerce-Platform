"""Fraud detection tests (P2.9): scoring rules, order holds, review workflow."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.fraud.models import FraudCheck
from apps.orders.models import Order, OrderStatus

from .conftest import confirm, enable_high_value, place_order

pytestmark = pytest.mark.django_db

CHECKS = reverse("v1:fraud:check-list")


def _check(order_id) -> FraudCheck:
    return FraudCheck.objects.get(order_id=order_id)


def _clear_url(check_id):
    return reverse("v1:fraud:check-clear", kwargs={"check_id": check_id})


def _reject_url(check_id):
    return reverse("v1:fraud:check-reject", kwargs={"check_id": check_id})


def test_default_order_is_approved_and_confirms(make_store, buyer_setup):
    store, _owner = make_store()
    client, _buyer, variant = buyer_setup(store)
    order = place_order(client, variant)
    assert confirm(client, order["id"]).status_code == 200
    check = _check(order["id"])
    assert check.decision == "approve"
    assert check.resolution == "cleared"


def test_high_value_holds_and_blocks_confirm(make_store, buyer_setup, settings):
    enable_high_value(settings, threshold="100", score=60)
    store, _owner = make_store()
    client, _buyer, variant = buyer_setup(store, price="100.00")
    order = place_order(client, variant)  # total 100 -> score 60 -> review
    assert _check(order["id"]).decision == "review"
    resp = confirm(client, order["id"])
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "order_on_hold"


def test_reject_threshold_decision(make_store, buyer_setup, settings):
    enable_high_value(settings, threshold="100", score=100, review=50, reject=100)
    store, _owner = make_store()
    client, _buyer, variant = buyer_setup(store, price="100.00")
    order = place_order(client, variant)  # score 100 -> reject
    assert _check(order["id"]).decision == "reject"
    assert confirm(client, order["id"]).status_code == 422


def test_velocity_rule_flags_repeat_orders(make_store, buyer_setup, settings):
    settings.FRAUD = {
        **settings.FRAUD,
        "VELOCITY_MAX_ORDERS": 1,
        "VELOCITY_SCORE": 60,
        "VELOCITY_WINDOW_MINUTES": 10,
        "REVIEW_THRESHOLD": 50,
    }
    store, _owner = make_store()
    client, _buyer, variant = buyer_setup(store)
    first = place_order(client, variant)  # count 1 -> approve
    second = place_order(client, variant)  # count 2 > 1 -> review
    assert _check(first["id"]).decision == "approve"
    assert _check(second["id"]).decision == "review"


def test_new_account_rule_flags(make_store, buyer_setup, settings):
    settings.FRAUD = {
        **settings.FRAUD,
        "NEW_ACCOUNT_MINUTES": 60,
        "NEW_ACCOUNT_SCORE": 60,
        "REVIEW_THRESHOLD": 50,
    }
    store, _owner = make_store()
    client, _buyer, variant = buyer_setup(store)
    order = place_order(client, variant)  # account created moments ago
    check = _check(order["id"])
    assert check.decision == "review"
    assert check.reasons  # carries a human-readable reason


def test_clear_releases_hold_then_confirm_succeeds(make_store, buyer_setup, store_client, settings):
    enable_high_value(settings, threshold="100", score=60)
    store, owner = make_store()
    client, _buyer, variant = buyer_setup(store, price="100.00")
    order = place_order(client, variant)
    check = _check(order["id"])
    cleared = store_client(owner, store).post(_clear_url(check.id))
    assert cleared.status_code == 200
    assert cleared.json()["data"]["resolution"] == "cleared"
    assert confirm(client, order["id"]).status_code == 200


def test_reject_cancels_the_order(make_store, buyer_setup, store_client, settings):
    enable_high_value(settings, threshold="100", score=60)
    store, owner = make_store()
    client, _buyer, variant = buyer_setup(store, price="100.00")
    order = place_order(client, variant)
    check = _check(order["id"])
    rejected = store_client(owner, store).post(_reject_url(check.id))
    assert rejected.status_code == 200
    assert rejected.json()["data"]["resolution"] == "rejected"
    assert Order.objects.get(id=order["id"]).status == OrderStatus.CANCELLED


def test_review_queue_lists_flagged(make_store, buyer_setup, store_client, settings):
    enable_high_value(settings, threshold="100", score=60)
    store, owner = make_store()
    client, _buyer, variant = buyer_setup(store, price="100.00")
    order = place_order(client, variant)
    queue = store_client(owner, store).get(CHECKS, {"decision": "review"}).json()["data"]
    assert [c["order"] for c in queue] == [order["id"]]


def test_employee_cannot_review(
    make_store, buyer_setup, make_user, add_member, store_client, settings
):
    from apps.stores.models import StoreRole

    enable_high_value(settings, threshold="100", score=60)
    store, _owner = make_store()
    client, _buyer, variant = buyer_setup(store, price="100.00")
    order = place_order(client, variant)
    check = _check(order["id"])
    employee = make_user()
    add_member(store, employee, StoreRole.EMPLOYEE)
    assert store_client(employee, store).post(_clear_url(check.id)).status_code == 403


def test_fraud_checks_are_store_scoped(make_store, buyer_setup, store_client, settings):
    enable_high_value(settings, threshold="100", score=60)
    store_a, _owner_a = make_store(name="A")
    store_b, owner_b = make_store(name="B")
    client_a, _buyer, variant_a = buyer_setup(store_a, price="100.00")
    place_order(client_a, variant_a)
    assert FraudCheck.objects.filter(store=store_a).exists()
    assert store_client(owner_b, store_b).get(CHECKS).json()["data"] == []
