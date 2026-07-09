"""Shipping tests (P2.8)."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.shipping.models import ShippingZone
from apps.stores.models import StoreRole

pytestmark = pytest.mark.django_db

ZONES = reverse("v1:shipping:zone-list")
METHODS = reverse("v1:shipping:available-methods")
CART_ADD = reverse("v1:cart:item-add")
CHECKOUT = reverse("v1:cart:checkout")


def _checkout(client, variant, *, qty=1, method=None, country="DE"):
    client.post(CART_ADD, {"variant_id": str(variant.id), "quantity": qty}, format="json")
    body = {}
    if method is not None:
        body = {"shipping_method_id": str(method.id), "country": country}
    return client.post(CHECKOUT, body, format="json")


def test_create_zone_and_method(store_client, make_store):
    store, owner = make_store()
    client = store_client(owner, store)
    zone = client.post(ZONES, {"name": "Europe", "countries": ["DE", "FR"]}, format="json")
    assert zone.status_code == 201
    method = client.post(
        reverse("v1:shipping:method-list", kwargs={"zone_id": zone.json()["data"]["id"]}),
        {"name": "Express", "price": "15.00"},
        format="json",
    )
    assert method.status_code == 201


def test_available_methods_for_country(store_client, make_store, make_user, shipping_method):
    store, _owner = make_store()
    shipping_method(store, countries=("DE",))
    resp = store_client(make_user(), store).get(METHODS, {"country": "DE"})
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["deliverable"] is True
    assert len(body["methods"]) == 1


def test_checkout_with_shipping_adds_cost(
    store_client, make_store, make_user, make_variant, shipping_method
):
    store, _owner = make_store()
    method = shipping_method(store, price="10.00", countries=("DE",))
    variant = make_variant(store, price="100.00")
    resp = _checkout(store_client(make_user(), store), variant, method=method, country="DE")
    data = resp.json()["data"]
    assert data["shipping_total"] == "10.00"
    assert data["total"] == "110.00"
    assert data["shipping_method"] == "Standard"


def test_checkout_without_shipping_is_unchanged(store_client, make_store, make_user, make_variant):
    store, _owner = make_store()
    variant = make_variant(store, price="100.00")
    resp = _checkout(store_client(make_user(), store), variant)  # no method
    data = resp.json()["data"]
    assert data["shipping_total"] == "0.00"
    assert data["total"] == "100.00"


def test_free_over_threshold(store_client, make_store, make_user, make_variant, shipping_method):
    store, _owner = make_store()
    method = shipping_method(store, price="10.00", free_over="50.00", countries=("DE",))
    variant = make_variant(store, price="30.00")
    # Subtotal 30 < 50 -> shipping charged.
    below = _checkout(store_client(make_user(), store), variant, qty=1, method=method)
    assert below.json()["data"]["shipping_total"] == "10.00"
    # Subtotal 60 >= 50 -> free shipping.
    above = _checkout(store_client(make_user(), store), variant, qty=2, method=method)
    assert above.json()["data"]["shipping_total"] == "0.00"


def test_per_kg_pricing(store_client, make_store, make_user, make_variant, shipping_method):
    store, _owner = make_store()
    method = shipping_method(store, price="10.00", per_kg="5.00", countries=("DE",))
    variant = make_variant(store, price="30.00", weight="2.000")
    resp = _checkout(store_client(make_user(), store), variant, qty=1, method=method)
    # 10 base + 5 * 2kg = 20.
    assert resp.json()["data"]["shipping_total"] == "20.00"


def test_method_not_serviceable(store_client, make_store, make_user, make_variant, shipping_method):
    store, _owner = make_store()
    method = shipping_method(store, countries=("FR",))  # serves FR only
    variant = make_variant(store, price="100.00")
    resp = _checkout(store_client(make_user(), store), variant, method=method, country="DE")
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "method_not_serviceable"


def test_set_tracking(store_client, make_store, make_user, make_variant):
    store, owner = make_store()
    variant = make_variant(store, price="50.00")
    buyer = make_user()
    order = _checkout(store_client(buyer, store), variant).json()["data"]
    resp = store_client(owner, store).post(
        reverse("v1:shipping:order-tracking", kwargs={"order_id": order["id"]}),
        {"tracking_number": "TRACK123"},
        format="json",
    )
    assert resp.status_code == 200
    detail = store_client(buyer, store).get(
        reverse("v1:orders:detail", kwargs={"order_id": order["id"]})
    )
    assert detail.json()["data"]["tracking_number"] == "TRACK123"


# --- Geo (map / km-radius) zones -------------------------------------------
# A point ~2 km from the Cairo centre (inside a 10 km circle) and one ~40 km away.
NEAR = {"lat": "30.0500", "lng": "31.2400"}
FAR = {"lat": "30.4000", "lng": "31.2357"}


def test_geo_zone_available_inside_circle(store_client, make_store, make_user, geo_method):
    store, _owner = make_store()
    geo_method(store)
    resp = store_client(make_user(), store).get(METHODS, NEAR)
    body = resp.json()["data"]
    assert body["deliverable"] is True
    assert len(body["methods"]) == 1
    # The circle is returned so the checkout map can draw coverage.
    assert len(body["geo_zones"]) == 1
    assert body["geo_zones"][0]["radius_km"] == 10.0


def test_geo_zone_unavailable_outside_circle(store_client, make_store, make_user, geo_method):
    store, _owner = make_store()
    geo_method(store)  # only a 10 km circle, no default/country zone
    resp = store_client(make_user(), store).get(METHODS, FAR)
    body = resp.json()["data"]
    assert body["deliverable"] is False
    assert body["methods"] == []


def test_checkout_blocked_outside_geo_zone(
    store_client, make_store, make_user, make_variant, geo_method
):
    store, _owner = make_store()
    geo_method(store)
    variant = make_variant(store, price="100.00")
    client = store_client(make_user(), store)
    client.post(CART_ADD, {"variant_id": str(variant.id), "quantity": 1}, format="json")
    resp = client.post(CHECKOUT, FAR, format="json")
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "delivery_unavailable"


def test_checkout_inside_geo_zone_succeeds(
    store_client, make_store, make_user, make_variant, geo_method
):
    store, _owner = make_store()
    method = geo_method(store, price="20.00")
    variant = make_variant(store, price="100.00")
    client = store_client(make_user(), store)
    client.post(CART_ADD, {"variant_id": str(variant.id), "quantity": 1}, format="json")
    body = {"shipping_method_id": str(method.id), **NEAR}
    resp = client.post(CHECKOUT, body, format="json")
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["shipping_total"] == "20.00"
    assert data["total"] == "120.00"


def test_checkout_blocked_when_store_suspended(
    store_client, make_store, make_user, make_variant
):
    from apps.stores.models import StoreStatus

    store, _owner = make_store()
    store.status = StoreStatus.SUSPENDED
    store.save(update_fields=["status"])
    variant = make_variant(store, price="50.00")
    resp = _checkout(store_client(make_user(), store), variant)
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "store_unavailable"


def test_employee_cannot_create_zone(store_client, make_store, make_user, add_member):
    store, _owner = make_store()
    employee = make_user()
    add_member(store, employee, StoreRole.EMPLOYEE)
    resp = store_client(employee, store).post(ZONES, {"name": "X"}, format="json")
    assert resp.status_code == 403


def test_zones_are_store_scoped(make_store):
    store_a, _owner_a = make_store(name="A")
    store_b, _owner_b = make_store(name="B")
    ShippingZone.objects.create(store=store_a, name="Z", code="z")
    assert ShippingZone.objects.filter(store=store_a).count() == 1
    assert ShippingZone.objects.filter(store=store_b).count() == 0
