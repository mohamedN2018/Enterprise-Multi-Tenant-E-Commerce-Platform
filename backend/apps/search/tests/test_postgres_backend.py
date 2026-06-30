"""Postgres FTS backend tests (P2.10 follow-up).

Backend pluggability is checked everywhere; the actual full-text query runs only
on PostgreSQL (skipped on the SQLite default).
"""

from __future__ import annotations

import pytest
from django.db import connection

from apps.catalog.models import ProductStatus
from apps.search.backends import PostgresSearchBackend, get_search_backend
from apps.search.services import ProductSearchService

pytestmark = pytest.mark.django_db


def test_backend_selection_is_pluggable(settings):
    settings.SEARCH = {**settings.SEARCH, "BACKEND": "apps.search.backends.PostgresSearchBackend"}
    assert isinstance(get_search_backend(), PostgresSearchBackend)


@pytest.mark.skipif(
    connection.vendor != "postgresql", reason="requires PostgreSQL full-text search"
)
def test_postgres_fts_ranks_and_filters(make_store, make_product, settings):
    settings.SEARCH = {**settings.SEARCH, "BACKEND": "apps.search.backends.PostgresSearchBackend"}
    store = make_store()
    shoes = make_product(store, name="Blue Running Shoes", description="comfortable trainers")
    make_product(store, name="Red Hat", description="a wide-brimmed hat")
    make_product(store, name="Hidden Shoes", description="x", status=ProductStatus.DRAFT)

    results = ProductSearchService().search(store=store, query="shoes")
    assert [row["id"] for row in results] == [str(shoes.id)]  # FTS match, draft excluded
