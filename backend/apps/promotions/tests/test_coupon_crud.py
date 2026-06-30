"""Coupon management (staff) tests."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.promotions.models import Coupon
from apps.promotions.services import PromotionService
from apps.stores.models import StoreRole

pytestmark = pytest.mark.django_db

COUPONS = reverse("v1:promotions:coupon-list")


def test_create_coupon_uppercases_code(store_client, make_store):
    store, owner = make_store()
    resp = store_client(owner, store).post(
        COUPONS,
        {"code": "save10", "discount_type": "percentage", "value": "10"},
        format="json",
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["code"] == "SAVE10"
    assert Coupon.objects.filter(store=store, code="SAVE10").exists()


def test_duplicate_code_conflict(store_client, make_store, make_coupon):
    store, owner = make_store()
    make_coupon(store, code="DUP")
    resp = store_client(owner, store).post(
        COUPONS,
        {"code": "dup", "discount_type": "fixed", "value": "5"},
        format="json",
    )
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "code_taken"


def test_percentage_over_100_rejected(store_client, make_store):
    store, owner = make_store()
    resp = store_client(owner, store).post(
        COUPONS,
        {"code": "BIG", "discount_type": "percentage", "value": "150"},
        format="json",
    )
    assert resp.status_code == 400


def test_employee_cannot_create_coupon(store_client, make_store, make_user, add_member):
    store, _owner = make_store()
    employee = make_user()
    add_member(store, employee, StoreRole.EMPLOYEE)
    resp = store_client(employee, store).post(
        COUPONS,
        {"code": "X", "discount_type": "fixed", "value": "5"},
        format="json",
    )
    assert resp.status_code == 403


def test_coupons_are_store_scoped(store_client, make_store, make_coupon):
    store_a, owner_a = make_store(name="A")
    store_b, owner_b = make_store(name="B")
    PromotionService().create_coupon(
        store=store_a, data={"code": "AONLY", "discount_type": "fixed", "value": "5"}
    )
    assert store_client(owner_b, store_b).get(COUPONS).json()["meta"]["pagination"]["count"] == 0
    assert store_client(owner_a, store_a).get(COUPONS).json()["meta"]["pagination"]["count"] == 1
