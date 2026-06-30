"""Address book tests (E2): CRUD, single default, and checkout snapshot."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.finance.services import TaxService

pytestmark = pytest.mark.django_db

ADDRESSES = reverse("v1:addresses:list")


def _payload(*, label="Home", country="DE", is_default=False):
    return {
        "label": label,
        "full_name": "Jane Doe",
        "line1": "1 Main St",
        "city": "Berlin",
        "country": country,
        "is_default": is_default,
    }


def _detail(address_id):
    return reverse("v1:addresses:detail", kwargs={"address_id": address_id})


def test_create_address(make_store, make_user, store_client):
    store, _owner = make_store()
    resp = store_client(make_user(), store).post(ADDRESSES, _payload(), format="json")
    assert resp.status_code == 201
    assert resp.json()["data"]["country"] == "DE"


def test_single_default_is_enforced(make_store, make_user, store_client):
    store, _owner = make_store()
    client = store_client(make_user(), store)
    client.post(ADDRESSES, _payload(label="A", is_default=True), format="json")
    second = client.post(ADDRESSES, _payload(label="B", is_default=True), format="json").json()[
        "data"
    ]
    defaults = [a["id"] for a in client.get(ADDRESSES).json()["data"] if a["is_default"]]
    assert defaults == [second["id"]]


def test_set_default_endpoint(make_store, make_user, store_client):
    store, _owner = make_store()
    client = store_client(make_user(), store)
    first = client.post(ADDRESSES, _payload(label="A", is_default=True), format="json").json()[
        "data"
    ]
    second = client.post(ADDRESSES, _payload(label="B"), format="json").json()["data"]
    client.post(reverse("v1:addresses:set-default", kwargs={"address_id": second["id"]}))
    flags = {a["id"]: a["is_default"] for a in client.get(ADDRESSES).json()["data"]}
    assert flags[second["id"]] is True
    assert flags[first["id"]] is False


def test_addresses_are_user_scoped(make_store, make_user, store_client):
    store, _owner = make_store()
    address = (
        store_client(make_user(), store).post(ADDRESSES, _payload(), format="json").json()["data"]
    )
    other = store_client(make_user(), store)
    assert other.get(ADDRESSES).json()["data"] == []
    assert other.get(_detail(address["id"])).status_code == 404


def test_delete_address(make_store, make_user, store_client):
    store, _owner = make_store()
    client = store_client(make_user(), store)
    address = client.post(ADDRESSES, _payload(), format="json").json()["data"]
    assert client.delete(_detail(address["id"])).status_code in (200, 204)
    assert client.get(ADDRESSES).json()["data"] == []


def test_checkout_snapshots_address_and_drives_tax(
    make_store, make_user, make_variant, store_client
):
    store, _owner = make_store()
    zone = TaxService().create_zone(store=store, data={"name": "EU", "countries": ["DE"]})
    TaxService().add_rate(store=store, zone=zone, data={"name": "VAT", "rate": Decimal("19")})
    variant = make_variant(store, price="100.00")
    client = store_client(make_user(), store)
    address = client.post(ADDRESSES, _payload(country="DE"), format="json").json()["data"]
    client.post(
        reverse("v1:cart:item-add"), {"variant_id": str(variant.id), "quantity": 1}, format="json"
    )
    order = client.post(
        reverse("v1:cart:checkout"), {"address_id": address["id"]}, format="json"
    ).json()["data"]
    assert order["shipping_address"]["city"] == "Berlin"
    assert order["shipping_address"]["country"] == "DE"
    assert order["tax_total"] == "19.00"  # the address country drove destination tax


def test_checkout_without_address_is_unchanged(make_store, make_user, make_variant, store_client):
    store, _owner = make_store()
    variant = make_variant(store, price="100.00")
    client = store_client(make_user(), store)
    client.post(
        reverse("v1:cart:item-add"), {"variant_id": str(variant.id), "quantity": 1}, format="json"
    )
    order = client.post(reverse("v1:cart:checkout"), {}, format="json").json()["data"]
    assert order["shipping_address"] == {}
    assert order["total"] == "100.00"
