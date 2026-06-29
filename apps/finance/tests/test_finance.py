"""Tax engine + multi-currency tests (P2.4)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.finance.models import Currency
from apps.finance.services import CurrencyService, TaxService
from apps.stores.models import StoreRole

pytestmark = pytest.mark.django_db

TAX_ZONES = reverse("v1:finance:tax-zone-list")
CURRENCIES = reverse("v1:finance:currency-list")
EXCHANGE = reverse("v1:finance:exchange-rate-list")
CONVERT = reverse("v1:finance:convert")
CART_ADD = reverse("v1:cart:item-add")
CHECKOUT = reverse("v1:cart:checkout")


def _zone_with_rate(store, *, name="DE", countries=("DE",), rate="20.000", is_default=False):
    service = TaxService()
    zone = service.create_zone(
        store=store,
        data={"name": name, "countries": list(countries), "is_default": is_default},
    )
    service.add_rate(store=store, zone=zone, data={"name": "VAT", "rate": Decimal(rate)})
    return zone


# --- Tax ---
def test_create_tax_zone_autocode(store_client, make_store):
    store, owner = make_store()
    resp = store_client(owner, store).post(
        TAX_ZONES, {"name": "European Union", "countries": ["DE", "FR"]}, format="json"
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["code"] == "european-union"


def test_resolve_rate_by_country(make_store):
    store, _owner = make_store()
    _zone_with_rate(store, countries=("DE",), rate="20.000")
    assert TaxService().resolve_rate(store=store, country="DE") == Decimal("20.000")


def test_resolve_rate_falls_back_to_flat_default(make_store):
    store, _owner = make_store()
    store.settings.default_tax_rate = Decimal("7")
    store.settings.save(update_fields=["default_tax_rate"])
    # No zones -> the store's flat rate is used.
    assert TaxService().resolve_rate(store=store, country="DE") == Decimal("7")


def test_checkout_uses_zone_rate(store_client, make_store, make_user, make_variant):
    store, _owner = make_store(country="DE")
    _zone_with_rate(store, countries=("DE",), rate="20.000")
    variant = make_variant(store, price="100.00")
    client = store_client(make_user(), store)
    client.post(CART_ADD, {"variant_id": str(variant.id), "quantity": 1}, format="json")

    order = client.post(CHECKOUT).json()["data"]
    assert order["subtotal"] == "100.00"
    assert order["tax_total"] == "20.00"
    assert order["total"] == "120.00"


def test_employee_cannot_create_zone(store_client, make_store, make_user, add_member):
    store, _owner = make_store()
    employee = make_user()
    add_member(store, employee, StoreRole.EMPLOYEE)
    resp = store_client(employee, store).post(TAX_ZONES, {"name": "X"}, format="json")
    assert resp.status_code == 403


def test_tax_zones_are_store_scoped(store_client, make_store):
    store_a, owner_a = make_store(name="A")
    store_b, owner_b = make_store(name="B")
    _zone_with_rate(store_a)
    assert store_client(owner_b, store_b).get(TAX_ZONES).json()["meta"]["pagination"]["count"] == 0
    assert store_client(owner_a, store_a).get(TAX_ZONES).json()["meta"]["pagination"]["count"] == 1


# --- Currency ---
def test_create_currency_and_duplicate(store_client, make_store):
    store, owner = make_store()
    client = store_client(owner, store)
    resp = client.post(CURRENCIES, {"code": "eur", "name": "Euro", "symbol": "€"}, format="json")
    assert resp.status_code == 201
    assert resp.json()["data"]["code"] == "EUR"
    dupe = client.post(CURRENCIES, {"code": "EUR"}, format="json")
    assert dupe.status_code == 409
    assert dupe.json()["error_code"] == "currency_exists"


def test_convert_direct(store_client, make_store):
    store, owner = make_store()
    store_client(owner, store).post(
        EXCHANGE, {"base_code": "USD", "target_code": "EUR", "rate": "0.90"}, format="json"
    )
    resp = store_client(owner, store).get(CONVERT, {"amount": "100", "from": "USD", "to": "EUR"})
    assert resp.status_code == 200
    assert resp.json()["data"]["converted"] == "90.00"


def test_convert_inverse(make_store):
    store, _owner = make_store()
    CurrencyService().create_exchange_rate(
        store=store, data={"base_code": "EUR", "target_code": "USD", "rate": Decimal("1.10")}
    )
    # No USD->EUR rate, so the inverse is used: 100 / 1.10 = 90.91.
    converted = CurrencyService().convert(
        store=store, amount=Decimal("100"), base_code="USD", target_code="EUR"
    )
    assert converted == Decimal("90.91")


def test_convert_same_currency(make_store):
    store, _owner = make_store()
    assert CurrencyService().convert(
        store=store, amount=Decimal("50"), base_code="USD", target_code="USD"
    ) == Decimal("50.00")


def test_convert_missing_pair(store_client, make_store):
    store, owner = make_store()
    resp = store_client(owner, store).get(CONVERT, {"amount": "10", "from": "USD", "to": "JPY"})
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "no_exchange_rate"


def test_currencies_are_store_scoped(make_store):
    store_a, _owner_a = make_store(name="A")
    store_b, _owner_b = make_store(name="B")
    Currency.objects.create(store=store_a, code="GBP")
    assert Currency.objects.filter(store=store_a).count() == 1
    assert Currency.objects.filter(store=store_b).count() == 0
