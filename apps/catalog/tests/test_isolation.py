"""Tenant isolation: catalog data must never leak across stores."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.catalog.services import CatalogService

pytestmark = pytest.mark.django_db

CATEGORY_LIST = reverse("v1:catalog:category-list")
PRODUCT_LIST = reverse("v1:catalog:product-list")


def test_list_is_scoped_to_active_store(store_client, make_store):
    store_a, owner_a = make_store(name="A")
    store_b, owner_b = make_store(name="B")
    CatalogService().create_category(store=store_a, data={"name": "A-only"})

    # Owner B, with B's context, sees none of A's categories.
    resp = store_client(owner_b, store_b).get(CATEGORY_LIST)
    assert resp.status_code == 200
    assert resp.json()["meta"]["pagination"]["count"] == 0

    # Owner A sees exactly one.
    resp_a = store_client(owner_a, store_a).get(CATEGORY_LIST)
    assert resp_a.json()["meta"]["pagination"]["count"] == 1


def test_cannot_retrieve_other_stores_object(store_client, make_store):
    store_a, _owner_a = make_store(name="A")
    store_b, owner_b = make_store(name="B")
    category_a = CatalogService().create_category(store=store_a, data={"name": "Secret"})

    url = reverse("v1:catalog:category-detail", kwargs={"category_id": category_a.id})
    # Owner B querying with B context cannot see A's category.
    resp = store_client(owner_b, store_b).get(url)
    assert resp.status_code == 404


def test_cannot_reference_other_stores_category(store_client, make_store):
    store_a, owner_a = make_store(name="A")
    store_b, _owner_b = make_store(name="B")
    category_b = CatalogService().create_category(store=store_b, data={"name": "B-cat"})

    # Owner A tries to attach B's category to an A product -> rejected.
    resp = store_client(owner_a, store_a).post(
        PRODUCT_LIST, {"name": "Cross", "category": str(category_b.id)}, format="json"
    )
    assert resp.status_code == 400
    assert "category" in resp.json()["errors"]
