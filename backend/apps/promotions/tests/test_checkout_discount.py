"""Coupon application to cart + checkout discount + redemption tests."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.promotions.models import CouponRedemption, DiscountType

from .conftest import add_to_cart

pytestmark = pytest.mark.django_db

COUPON_URL = reverse("v1:cart:coupon")
CART_URL = reverse("v1:cart:cart")
CHECKOUT = reverse("v1:cart:checkout")


def _apply(client, code):
    return client.post(COUPON_URL, {"code": code}, format="json")


def test_apply_valid_coupon_shows_discount(make_store, buyer_setup, make_coupon):
    store, _owner = make_store()
    make_coupon(store, code="SAVE10", value="10")  # 10%
    client, _buyer, variant = buyer_setup(store, price="50.00")
    add_to_cart(client, variant, 2)  # subtotal 100

    resp = _apply(client, "SAVE10")
    assert resp.status_code == 200
    cart = client.get(CART_URL).json()["data"]
    assert cart["coupon_code"] == "SAVE10"
    assert cart["discount"] == "10.00"
    assert cart["total"] == "90.00"


def test_apply_invalid_code(make_store, buyer_setup):
    store, _owner = make_store()
    client, _buyer, variant = buyer_setup(store)
    add_to_cart(client, variant, 1)
    resp = _apply(client, "NOPE")
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "coupon_invalid"


def test_min_spend_not_met(make_store, buyer_setup, make_coupon):
    store, _owner = make_store()
    make_coupon(store, code="BIG", value="10", min_spend=Decimal("500"))
    client, _buyer, variant = buyer_setup(store, price="50.00")
    add_to_cart(client, variant, 1)  # subtotal 50 < 500
    resp = _apply(client, "BIG")
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "min_spend_not_met"


def test_checkout_applies_percentage_discount_and_records_redemption(
    make_store, buyer_setup, make_coupon
):
    store, _owner = make_store()
    coupon = make_coupon(store, code="SAVE10", value="10")  # 10%
    client, buyer, variant = buyer_setup(store, price="50.00")
    add_to_cart(client, variant, 2)  # subtotal 100
    _apply(client, "SAVE10")

    order = client.post(CHECKOUT).json()["data"]
    assert order["subtotal"] == "100.00"
    assert order["discount_total"] == "10.00"
    assert order["total"] == "90.00"
    assert order["coupon_code"] == "SAVE10"

    coupon.refresh_from_db()
    assert coupon.used_count == 1
    assert CouponRedemption.objects.filter(
        coupon=coupon, user=buyer, amount=Decimal("10.00")
    ).exists()


def test_checkout_fixed_discount(make_store, buyer_setup, make_coupon):
    store, _owner = make_store()
    make_coupon(store, code="MINUS15", discount_type=DiscountType.FIXED, value="15")
    client, _buyer, variant = buyer_setup(store, price="50.00")
    add_to_cart(client, variant, 2)  # subtotal 100
    _apply(client, "MINUS15")
    order = client.post(CHECKOUT).json()["data"]
    assert order["discount_total"] == "15.00"
    assert order["total"] == "85.00"


def test_global_usage_limit_reached(make_store, buyer_setup, make_coupon):
    store, _owner = make_store()
    make_coupon(store, code="ONESHOT", value="10", usage_limit=1, used_count=1)
    client, _buyer, variant = buyer_setup(store)
    add_to_cart(client, variant, 1)
    resp = _apply(client, "ONESHOT")
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "coupon_exhausted"


def test_per_user_limit_enforced(make_store, buyer_setup, make_coupon):
    store, _owner = make_store()
    make_coupon(store, code="ONCE", value="10", per_user_limit=1)
    client, _buyer, variant = buyer_setup(store, price="50.00", stock=20)
    # First order with the coupon.
    add_to_cart(client, variant, 1)
    _apply(client, "ONCE")
    assert client.post(CHECKOUT).status_code == 201
    # Second attempt by the same buyer is blocked.
    add_to_cart(client, variant, 1)
    resp = _apply(client, "ONCE")
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "per_user_limit_reached"


def test_expired_coupon(make_store, buyer_setup, make_coupon):
    store, _owner = make_store()
    make_coupon(
        store,
        code="OLD",
        value="10",
        ends_at=timezone.now() - timedelta(days=1),
    )
    client, _buyer, variant = buyer_setup(store)
    add_to_cart(client, variant, 1)
    resp = _apply(client, "OLD")
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "coupon_expired"
