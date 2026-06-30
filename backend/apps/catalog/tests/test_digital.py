"""Digital product tests (P2.1b): assets, license keys, fulfillment, downloads."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.catalog.models import (
    DownloadGrant,
    LicenseKey,
    LicenseKeyStatus,
    ProductStatus,
    ProductType,
)
from apps.catalog.services import CatalogService, DigitalProductService
from apps.stores.models import StoreRole

pytestmark = pytest.mark.django_db

ADD_ITEM = reverse("v1:cart:item-add")
CHECKOUT = reverse("v1:cart:checkout")
DOWNLOADS = reverse("v1:downloads:list")


def _digital_url(variant_id):
    return reverse("v1:catalog:variant-digital", kwargs={"variant_id": variant_id})


def _keys_url(variant_id):
    return reverse("v1:catalog:variant-license-keys", kwargs={"variant_id": variant_id})


def _digital_variant(
    store, *, sku="DIG", price="9.99", requires_license=False, limit=None, keys=None
):
    cat = CatalogService()
    product = cat.create_product(
        store=store,
        data={
            "name": f"Digital {sku}",
            "product_type": ProductType.DIGITAL,
            "status": ProductStatus.PUBLISHED,
        },
    )
    variant = cat.create_variant(
        store=store, product=product, data={"sku": sku, "price": Decimal(price)}
    )
    DigitalProductService().upsert_asset(
        store=store,
        variant=variant,
        data={
            "external_url": "https://example.com/file.zip",
            "download_limit": limit,
            "requires_license": requires_license,
            "is_active": True,
        },
    )
    if keys:
        DigitalProductService().add_license_keys(store=store, variant=variant, keys=keys)
    return variant


def _buy_and_confirm(client, variant, qty=1):
    client.post(ADD_ITEM, {"variant_id": str(variant.id), "quantity": qty}, format="json")
    order = client.post(CHECKOUT).json()["data"]
    client.post(reverse("v1:orders:confirm", kwargs={"order_id": order["id"]}))
    return order


# --- Staff management ------------------------------------------------------
def test_upsert_digital_asset(store_client, make_store):
    store, owner = make_store()
    variant = CatalogService().create_variant(
        store=store,
        product=CatalogService().create_product(
            store=store, data={"name": "D", "product_type": ProductType.DIGITAL}
        ),
        data={"sku": "D1", "price": Decimal("5.00")},
    )
    resp = store_client(owner, store).put(
        _digital_url(variant.id),
        {"external_url": "https://x.test/f.zip", "download_limit": 5, "requires_license": True},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["download_limit"] == 5
    assert resp.json()["data"]["requires_license"] is True


def test_add_license_keys_and_duplicates(store_client, make_store):
    store, owner = make_store()
    variant = _digital_variant(store, sku="K", requires_license=True)
    client = store_client(owner, store)
    resp = client.post(_keys_url(variant.id), {"keys": ["AAA", "BBB"]}, format="json")
    assert resp.status_code == 201
    assert LicenseKey.objects.filter(variant=variant).count() == 2
    dupe = client.post(_keys_url(variant.id), {"keys": ["AAA"]}, format="json")
    assert dupe.status_code == 409
    assert dupe.json()["error_code"] == "duplicate_keys"


def test_employee_cannot_add_keys(store_client, make_store, make_user, add_member):
    store, _owner = make_store()
    variant = _digital_variant(store, sku="K", requires_license=True)
    employee = make_user()
    add_member(store, employee, StoreRole.EMPLOYEE)
    resp = store_client(employee, store).post(_keys_url(variant.id), {"keys": ["X"]}, format="json")
    assert resp.status_code == 403


# --- Buyer flow ------------------------------------------------------------
def test_digital_purchase_creates_download_grant(store_client, make_store, make_user):
    store, _owner = make_store()
    variant = _digital_variant(store, limit=3)
    client = store_client(make_user(), store)
    _buy_and_confirm(client, variant)

    grants = client.get(DOWNLOADS).json()
    assert grants["meta"]["pagination"]["count"] == 1
    grant = grants["data"][0]
    assert grant["download_limit"] == 3
    assert DownloadGrant.objects.count() == 1


def test_download_enforces_limit(store_client, make_store, make_user):
    store, _owner = make_store()
    variant = _digital_variant(store, limit=2)
    client = store_client(make_user(), store)
    _buy_and_confirm(client, variant)
    token = client.get(DOWNLOADS).json()["data"][0]["token"]
    url = reverse("v1:downloads:download", kwargs={"token": token})

    first = client.get(url)
    assert first.status_code == 200
    assert first.json()["data"]["remaining_downloads"] == 1
    assert client.get(url).status_code == 200  # second, remaining 0
    blocked = client.get(url)
    assert blocked.status_code == 422
    assert blocked.json()["error_code"] == "download_unavailable"


def test_license_assigned_on_purchase(store_client, make_store, make_user):
    store, _owner = make_store()
    variant = _digital_variant(store, requires_license=True, keys=["LIC-1", "LIC-2"])
    client = store_client(make_user(), store)
    _buy_and_confirm(client, variant, qty=1)

    grant = client.get(DOWNLOADS).json()["data"][0]
    assert len(grant["license_keys"]) == 1
    assert LicenseKey.objects.filter(variant=variant, status=LicenseKeyStatus.ASSIGNED).count() == 1
    assert (
        LicenseKey.objects.filter(variant=variant, status=LicenseKeyStatus.AVAILABLE).count() == 1
    )


def test_license_gated_availability_limits_cart(store_client, make_store, make_user):
    store, _owner = make_store()
    variant = _digital_variant(store, requires_license=True, keys=["ONLY-1"])
    client = store_client(make_user(), store)
    # Only one key -> can add 1, not 2.
    over = client.post(ADD_ITEM, {"variant_id": str(variant.id), "quantity": 2}, format="json")
    assert over.status_code == 422
    assert over.json()["error_code"] == "insufficient_stock"


def test_download_requires_ownership(store_client, make_store, make_user):
    store, _owner = make_store()
    variant = _digital_variant(store, limit=3)
    buyer = make_user()
    _buy_and_confirm(store_client(buyer, store), variant)
    token = DownloadGrant.objects.get().token

    other = store_client(make_user(), store)
    resp = other.get(reverse("v1:downloads:download", kwargs={"token": token}))
    assert resp.status_code == 404
