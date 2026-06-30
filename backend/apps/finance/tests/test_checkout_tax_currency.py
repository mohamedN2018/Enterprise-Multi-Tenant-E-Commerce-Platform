"""Destination tax + checkout currency tests (P2.4 follow-up)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.finance.services import CurrencyService, TaxService

pytestmark = pytest.mark.django_db

CART_ADD = reverse("v1:cart:item-add")
CHECKOUT = reverse("v1:cart:checkout")


def _checkout(client, variant, body, *, qty=1):
    client.post(CART_ADD, {"variant_id": str(variant.id), "quantity": qty}, format="json")
    return client.post(CHECKOUT, body, format="json")


def test_destination_tax_uses_checkout_country(make_store, make_user, make_variant, store_client):
    store, _owner = make_store()
    zone = TaxService().create_zone(store=store, data={"name": "EU", "countries": ["DE"]})
    TaxService().add_rate(store=store, zone=zone, data={"name": "VAT", "rate": Decimal("19")})
    variant = make_variant(store, price="100.00")

    # Destination DE -> 19% VAT.
    taxed = _checkout(store_client(make_user(), store), variant, {"country": "DE"}).json()["data"]
    assert taxed["tax_total"] == "19.00"
    assert taxed["total"] == "119.00"

    # Destination US -> no matching zone, store default rate (0).
    untaxed = _checkout(store_client(make_user(), store), variant, {"country": "US"}).json()["data"]
    assert untaxed["tax_total"] == "0.00"
    assert untaxed["total"] == "100.00"


def test_checkout_settles_in_selected_currency(make_store, make_user, make_variant, store_client):
    store, _owner = make_store()
    CurrencyService().create_exchange_rate(
        store=store,
        data={"base_code": store.currency, "target_code": "EUR", "rate": Decimal("0.9")},
    )
    variant = make_variant(store, price="100.00")
    order = _checkout(store_client(make_user(), store), variant, {"currency": "EUR"}).json()["data"]
    assert order["currency"] == "EUR"
    assert order["subtotal"] == "90.00"
    assert order["total"] == "90.00"


def test_unknown_currency_is_rejected(make_store, make_user, make_variant, store_client):
    store, _owner = make_store()  # store currency USD, no GBP rate
    variant = make_variant(store, price="100.00")
    resp = _checkout(store_client(make_user(), store), variant, {"currency": "GBP"})
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "no_exchange_rate"


def test_default_checkout_is_unchanged(make_store, make_user, make_variant, store_client):
    store, _owner = make_store()
    variant = make_variant(store, price="100.00")
    order = _checkout(store_client(make_user(), store), variant, {}).json()["data"]
    assert order["currency"] == store.currency
    assert order["tax_total"] == "0.00"
    assert order["total"] == "100.00"
