"""Outbound POS supplier link: verify the key, import & upsert the catalog."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.catalog.models import Product
from apps.catalog.services import CatalogService
from apps.inventory.models import StockItem
from apps.pos.client import PosAuthError, PosSupplierClient
from apps.stores.models import StoreRole

pytestmark = pytest.mark.django_db

SUPPLIER_URL = reverse("v1:pos:supplier")
IMPORT_URL = reverse("v1:pos:supplier-import")

STORE_SUMMARY = {"store": "سوبر ماركت النيل", "provider": "q-shop POS", "productCount": 46}
PRODUCTS = [
    {
        "id": "u-cola", "name": "كوكاكولا كانز 330 مل", "name_en": "Coca-Cola Cans 330ml",
        "description": None, "sku": None, "barcode": "5449000000996", "price": 12.0,
        "cost": 8.0, "stock": 34, "category": "المشروبات", "image_url": None,
        "type": "STANDARD", "is_active": True,
    },
    {
        "id": "u-chips", "name": "شيبسي", "name_en": "Chips", "description": None,
        "sku": None, "barcode": "6221031492891", "price": 10.0, "cost": 6.0, "stock": 5,
        "category": "سناكس", "image_url": None, "type": "STANDARD", "is_active": True,
    },
]

CONNECT_BODY = {
    "provider": "q-shop POS",
    "api_url": "https://q-shop-cashier.deplois.net/api",
    "api_key": "secret-key-123",
}


@pytest.fixture
def mock_pos(monkeypatch):
    """Stub the outbound HTTP client so no real network call happens."""
    monkeypatch.setattr(PosSupplierClient, "verify", lambda self: dict(STORE_SUMMARY))
    monkeypatch.setattr(PosSupplierClient, "fetch_products", lambda self: [dict(p) for p in PRODUCTS])


def _connect(store_client, store, owner):
    return store_client(owner, store).post(SUPPLIER_URL, CONNECT_BODY, format="json")


def _on_hand(store, sku):
    from apps.catalog.models import ProductVariant

    variant = ProductVariant.all_objects.get(store=store, sku=sku)
    return sum(i.quantity for i in StockItem.all_objects.filter(store=store, variant=variant))


# --- Connect ---------------------------------------------------------------
def test_connect_verifies_key_and_stores(store_client, make_store, mock_pos):
    store, owner = make_store()
    resp = _connect(store_client, store, owner)
    assert resp.status_code == 200, resp.content
    data = resp.json()["data"]
    assert data["is_connected"] is True
    assert data["remote_store_name"] == "سوبر ماركت النيل"
    assert data["remote_product_count"] == 46
    assert "api_key" not in data  # never exposed
    assert data["has_key"] is True


def test_connect_rejects_bad_key(store_client, make_store, monkeypatch):
    store, owner = make_store()

    def _boom(self):
        raise PosAuthError()

    monkeypatch.setattr(PosSupplierClient, "verify", _boom)
    resp = _connect(store_client, store, owner)
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "pos_invalid_key"


def test_employee_without_settings_cannot_connect(store_client, make_store, make_user, add_member, mock_pos):
    store, owner = make_store()
    employee = make_user()
    add_member(store, employee, StoreRole.EMPLOYEE, permissions=["catalog"])
    assert store_client(employee, store).post(SUPPLIER_URL, CONNECT_BODY, format="json").status_code == 403


# --- Import ----------------------------------------------------------------
def test_import_creates_products_with_price_and_stock(store_client, make_store, mock_pos):
    store, owner = make_store()
    _connect(store_client, store, owner)

    resp = store_client(owner, store).post(IMPORT_URL, {}, format="json")
    assert resp.status_code == 200, resp.content
    assert resp.json()["data"]["summary"] == {"created": 2, "updated": 0, "skipped": 0}

    assert Product.all_objects.filter(store=store, is_deleted=False).count() == 2
    # Price landed on the default variant; stock became real warehouse inventory.
    cola = Product.all_objects.get(store=store, name="كوكاكولا كانز 330 مل")
    variant = cola.variants.get(is_default=True)
    assert str(variant.price) == "12.00" and str(variant.cost_price) == "8.00"
    assert variant.barcode == "5449000000996"
    assert _on_hand(store, variant.sku) == 34
    # Category was created from the Arabic name.
    assert cola.category and cola.category.name == "المشروبات"


def test_reimport_updates_in_place(store_client, make_store, mock_pos, monkeypatch):
    store, owner = make_store()
    _connect(store_client, store, owner)
    store_client(owner, store).post(IMPORT_URL, {}, format="json")

    # Price + stock change upstream; a second import must update, not duplicate.
    bumped = [dict(p) for p in PRODUCTS]
    bumped[0] = {**bumped[0], "price": 15.5, "stock": 100}
    monkeypatch.setattr(PosSupplierClient, "fetch_products", lambda self: bumped)

    resp = store_client(owner, store).post(IMPORT_URL, {}, format="json")
    assert resp.json()["data"]["summary"] == {"created": 0, "updated": 2, "skipped": 0}
    assert Product.all_objects.filter(store=store, is_deleted=False).count() == 2

    cola = Product.all_objects.get(store=store, name="كوكاكولا كانز 330 مل")
    assert str(cola.variants.get(is_default=True).price) == "15.50"
    assert _on_hand(store, cola.variants.get(is_default=True).sku) == 100


def test_import_matches_existing_by_barcode(store_client, make_store, mock_pos):
    store, owner = make_store()
    # A product already exists locally with the same barcode as an incoming one.
    product = CatalogService().create_product(store=store, data={"name": "كولا قديمة"})
    CatalogService().create_variant(
        store=store,
        product=product,
        data={"sku": "OLD-1", "barcode": "5449000000996", "price": "9.00", "is_default": True},
    )
    _connect(store_client, store, owner)

    store_client(owner, store).post(IMPORT_URL, {}, format="json")

    # The barcode match links to the existing product — no duplicate created.
    assert (
        Product.all_objects.filter(store=store, is_deleted=False, variants__barcode="5449000000996")
        .distinct()
        .count()
        == 1
    )
