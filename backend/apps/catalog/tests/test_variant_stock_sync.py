"""Setting a variant's stock from the product form must create real warehouse
inventory, so the storefront actually reports the product as available.

Regression: a variant saved with ``stock_quantity`` but no ``StockItem`` read as
out of stock ("غير متاح حاليًا") because availability is gated by warehouse
on-hand, not the denormalised field.
"""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.catalog.models import Product, ProductVariant
from apps.catalog.services import CatalogService
from apps.inventory.models import StockItem
from apps.stores.models import StoreRole

pytestmark = pytest.mark.django_db

PRODUCT_LIST = reverse("v1:catalog:product-list")


def _variant_url(product_id):
    return reverse("v1:catalog:variant-list", kwargs={"product_id": product_id})


def test_create_variant_with_stock_creates_warehouse_inventory(make_store):
    store, owner = make_store()
    product = CatalogService().create_product(store=store, data={"name": "Widget"})

    variant = CatalogService().create_variant(
        store=store,
        product=product,
        data={"sku": "W-1", "price": "50.00", "stock_quantity": 7, "is_default": True},
    )

    item = StockItem.objects.get(store=store, variant=variant)
    assert item.quantity == 7
    assert item.warehouse.is_default or item.warehouse.code == "MAIN"


def test_zero_stock_product_saves_in_store_warehouse(make_store):
    """Adding a product with no stock still saves normally and gets a store-owned
    warehouse record (0 on-hand) — the store's own inventory, independent of any
    POS. It simply reads as out of stock until quantity is added."""
    store, owner = make_store()
    product = CatalogService().create_product(store=store, data={"name": "Preorder"})

    variant = CatalogService().create_variant(
        store=store,
        product=product,
        data={"sku": "PRE-1", "price": "99.00", "stock_quantity": 0, "is_default": True},
    )

    item = StockItem.objects.get(store=store, variant=variant)
    assert item.quantity == 0
    # The warehouse belongs to THIS store (its default) — not tied to the cashier.
    assert item.warehouse.store_id == store.id
    assert item.warehouse.is_default or item.warehouse.code == "MAIN"


def test_update_variant_stock_adjusts_inventory(make_store):
    store, owner = make_store()
    product = CatalogService().create_product(store=store, data={"name": "Widget"})
    variant = CatalogService().create_variant(
        store=store,
        product=product,
        data={"sku": "W-1", "price": "50.00", "stock_quantity": 3, "is_default": True},
    )

    CatalogService().update_variant(instance=variant, data={"stock_quantity": 20})

    assert StockItem.objects.get(store=store, variant=variant).quantity == 20


def test_storefront_reports_in_stock_after_form_save(store_client, make_store):
    """End to end through the API: a published product whose default variant was
    given a quantity reads as ``in_stock`` on the public storefront."""
    store, owner = make_store()
    client = store_client(owner, store)

    product_id = client.post(
        PRODUCT_LIST, {"name": "Real Product", "status": "published"}, format="json"
    ).json()["data"]["id"]
    resp = client.post(
        _variant_url(product_id),
        {"sku": "REAL-1", "price": "99.00", "stock_quantity": 5, "is_default": True},
        format="json",
    )
    assert resp.status_code == 201

    detail = client.get(
        reverse("v1:storefront:product-detail", kwargs={"product_id": product_id})
    ).json()["data"]
    default = next(v for v in detail["variants"] if v["is_default"])
    assert default["in_stock"] is True


def test_untracked_variant_needs_no_stock_record(make_store):
    """Digital / untracked variants are always available, so no StockItem is made."""
    store, owner = make_store()
    product = CatalogService().create_product(store=store, data={"name": "E-book"})

    variant = CatalogService().create_variant(
        store=store,
        product=product,
        data={
            "sku": "EB-1",
            "price": "10.00",
            "stock_quantity": 0,
            "track_inventory": False,
            "is_default": True,
        },
    )

    assert not StockItem.objects.filter(store=store, variant=variant).exists()


def test_stock_sync_never_drops_below_reserved(make_store):
    """Lowering the form quantity below what carts already hold must not oversell."""
    from apps.inventory.services import InventoryService

    store, owner = make_store()
    product = CatalogService().create_product(store=store, data={"name": "Widget"})
    variant = CatalogService().create_variant(
        store=store,
        product=product,
        data={"sku": "W-1", "price": "50.00", "stock_quantity": 10, "is_default": True},
    )
    warehouse = StockItem.objects.get(store=store, variant=variant).warehouse
    InventoryService().reserve(store=store, variant=variant, warehouse=warehouse, quantity=4)

    # Seller tries to set stock to 1, but 4 are reserved — floor at the reserved amount.
    CatalogService().update_variant(instance=variant, data={"stock_quantity": 1})

    assert StockItem.objects.get(store=store, variant=variant).quantity == 4
