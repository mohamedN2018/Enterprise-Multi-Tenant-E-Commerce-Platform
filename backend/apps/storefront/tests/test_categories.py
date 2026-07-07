"""Storefront category list: dedup by name, one representative English label."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.catalog.models import Category

pytestmark = pytest.mark.django_db

CATEGORIES = reverse("v1:storefront:categories")


def _categorised_product(active_store, make_product, *, store_name, name_en, slug, prod_slug):
    store = active_store(name="متجر", name_en=store_name)
    category = Category.objects.create(
        store=store, name="ملابس", name_en=name_en, slug="clothing", is_active=True
    )
    product = make_product(
        store,
        name="قميص",
        name_en="Shirt",
        description="د",
        description_en="d",
        slug=prod_slug,
    )
    product.category = category
    product.save(update_fields=["category"])
    return store


def test_same_category_across_stores_is_merged(active_store, make_product):
    # Store A has the English label; store B left it blank.
    _categorised_product(active_store, make_product, store_name="A", name_en="Clothing", slug="a", prod_slug="a")
    _categorised_product(active_store, make_product, store_name="B", name_en="", slug="b", prod_slug="b")

    data = APIClient().get(CATEGORIES).json()["data"]
    rows = [r for r in data if r["name"] == "ملابس"]

    assert len(rows) == 1  # one row, not split by differing name_en
    assert rows[0]["name_en"] == "Clothing"  # the non-empty translation wins
    assert rows[0]["product_count"] == 2  # summed across both stores


def test_category_without_products_is_hidden(active_store, make_product):
    store = active_store()
    Category.objects.create(store=store, name="فارغ", name_en="Empty", slug="empty", is_active=True)

    names = [r["name"] for r in APIClient().get(CATEGORIES).json()["data"]]
    assert "فارغ" not in names
