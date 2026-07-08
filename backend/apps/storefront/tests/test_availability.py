"""Storefront stock signalling: an ``in_stock`` flag on every product, plus an
``?in_stock=1`` filter so sold-out products can be hidden (e.g. on the home page).
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.catalog.services import CatalogService

pytestmark = pytest.mark.django_db

LIST_URL = reverse("v1:storefront:products")


def _detail(product):
    url = reverse("v1:storefront:product-detail", kwargs={"product_id": product.id})
    return APIClient().get(url).json()["data"]


def _list(**params):
    return APIClient().get(LIST_URL, params).json()["data"]


def _product(active_store, make_product, slug):
    store = active_store(name=f"متجر-{slug}", name_en=f"Shop {slug}")
    product = make_product(
        store, name=slug, name_en=slug, description="د", description_en="d", slug=slug
    )
    return store, product


def test_in_stock_product_is_flagged_and_listed(active_store, make_product):
    store, product = _product(active_store, make_product, "instock")
    CatalogService().create_variant(
        store=store,
        product=product,
        data={"sku": "IN-1", "price": "10.00", "stock_quantity": 5, "is_default": True},
    )

    assert _detail(product)["in_stock"] is True
    ids = [p["id"] for p in _list(in_stock=1)]
    assert str(product.id) in ids


def test_sold_out_product_flagged_but_hidden_when_filtered(active_store, make_product):
    store, product = _product(active_store, make_product, "soldout")
    CatalogService().create_variant(
        store=store,
        product=product,
        data={"sku": "OUT-1", "price": "10.00", "stock_quantity": 0, "is_default": True},
    )

    # Still visible in the default listing, but marked out of stock...
    assert _detail(product)["in_stock"] is False
    assert str(product.id) in [p["id"] for p in _list()]
    # ...and excluded once the caller asks for in-stock only.
    assert str(product.id) not in [p["id"] for p in _list(in_stock=1)]


def test_available_quantity_is_exposed_for_capping(active_store, make_product):
    """The storefront reports the exact sellable count so the buyer can't order
    more than what's in stock; untracked variants report null (unlimited)."""
    store, product = _product(active_store, make_product, "capqty")
    CatalogService().create_variant(
        store=store,
        product=product,
        data={"sku": "CAP-1", "price": "10.00", "stock_quantity": 5, "is_default": True},
    )
    variant = _detail(product)["variants"][0]
    assert variant["available"] == 5

    store2, product2 = _product(active_store, make_product, "capdigital")
    CatalogService().create_variant(
        store=store2,
        product=product2,
        data={"sku": "CAP-D", "price": "10.00", "track_inventory": False, "is_default": True},
    )
    assert _detail(product2)["variants"][0]["available"] is None


def test_untracked_variant_is_always_in_stock(active_store, make_product):
    store, product = _product(active_store, make_product, "digital")
    CatalogService().create_variant(
        store=store,
        product=product,
        data={
            "sku": "DIG-1",
            "price": "10.00",
            "stock_quantity": 0,
            "track_inventory": False,
            "is_default": True,
        },
    )

    assert _detail(product)["in_stock"] is True
    assert str(product.id) in [p["id"] for p in _list(in_stock=1)]
