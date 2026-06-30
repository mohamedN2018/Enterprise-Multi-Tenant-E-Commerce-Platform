"""Product search tests (P2.10): matching, filters, scoping, cache invalidation."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.catalog.models import ProductStatus
from apps.search.services import ProductSearchService

pytestmark = pytest.mark.django_db

SEARCH = reverse("v1:search:product-search")


def _ids(response):
    return {row["id"] for row in response.json()["data"]}


def test_search_matches_published_by_name(make_store, store_client, make_product):
    store = make_store()
    shirt = make_product(store, name="Blue Shirt")
    make_product(store, name="Red Hat")
    client = store_client(store)
    assert _ids(client.get(SEARCH, {"q": "shirt"})) == {str(shirt.id)}
    assert _ids(client.get(SEARCH, {"q": "sock"})) == set()


def test_search_matches_by_sku(make_store, store_client, make_product):
    store = make_store()
    product = make_product(store, name="Widget", sku="ZX-9000")
    assert _ids(store_client(store).get(SEARCH, {"q": "zx-9000"})) == {str(product.id)}


def test_unpublished_products_are_excluded(make_store, store_client, make_product):
    store = make_store()
    make_product(store, name="Secret", status=ProductStatus.DRAFT)
    assert _ids(store_client(store).get(SEARCH, {"q": "secret"})) == set()


def test_price_filters(make_store, store_client, make_product):
    store = make_store()
    make_product(store, name="Cheap Thing", price="10.00")
    pricey = make_product(store, name="Pricey Thing", price="100.00")
    client = store_client(store)
    result = client.get(SEARCH, {"q": "thing", "min_price": "50"})
    assert _ids(result) == {str(pricey.id)}


def test_results_are_store_scoped(make_store, store_client, make_product):
    store_a = make_store(name="A")
    store_b = make_store(name="B")
    make_product(store_a, name="Alpha Widget")
    assert _ids(store_client(store_b).get(SEARCH, {"q": "widget"})) == set()


def test_results_cached_then_invalidated_on_catalog_write(make_store, store_client, make_product):
    store = make_store()
    make_product(store, name="Gadget One")
    client = store_client(store)
    assert len(client.get(SEARCH, {"q": "gadget"}).json()["data"]) == 1
    # A new matching product bumps the store's search version -> cache miss.
    make_product(store, name="Gadget Two")
    assert len(client.get(SEARCH, {"q": "gadget"}).json()["data"]) == 2


def test_service_caches_within_a_version(make_store, make_product):
    store = make_store()
    make_product(store, name="Cached Item")
    service = ProductSearchService()
    first = service.search(store=store, query="cached")
    version = ProductSearchService.version(store)
    second = service.search(store=store, query="cached")
    assert first == second
    # No catalog write happened, so the version is unchanged (cache stayed valid).
    assert ProductSearchService.version(store) == version
