"""Storefront serves content in the request's language (Arabic-first).

Regression cover for the detail views, which build serializers by hand and must
pass the request into serializer context for ``Accept-Language`` to take effect.
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def _product(active_store, make_product):
    store = active_store(name="متجر التجربة", name_en="Demo Store")
    product = make_product(
        store,
        name="سماعات لاسلكية",
        name_en="Wireless Headphones",
        description="سماعات بجودة عالية.",
        description_en="High quality headphones.",
        slug="wireless-headphones",
    )
    return store, product


def test_product_detail_defaults_to_arabic(active_store, make_product):
    _store, product = _product(active_store, make_product)
    url = reverse("v1:storefront:product-detail", kwargs={"product_id": product.id})

    data = APIClient().get(url).json()["data"]

    assert data["name"] == "سماعات لاسلكية"
    assert data["description"] == "سماعات بجودة عالية."


def test_product_detail_english_when_requested(active_store, make_product):
    _store, product = _product(active_store, make_product)
    url = reverse("v1:storefront:product-detail", kwargs={"product_id": product.id})

    data = APIClient().get(url, HTTP_ACCEPT_LANGUAGE="en-US,en").json()["data"]

    assert data["name"] == "Wireless Headphones"
    assert data["description"] == "High quality headphones."


def test_store_detail_english_when_requested(active_store, make_product):
    store, _prod = _product(active_store, make_product)
    url = reverse("v1:storefront:store-detail", kwargs={"slug": store.slug})

    data = APIClient().get(url, HTTP_ACCEPT_LANGUAGE="en").json()["data"]

    assert data["name"] == "Demo Store"
