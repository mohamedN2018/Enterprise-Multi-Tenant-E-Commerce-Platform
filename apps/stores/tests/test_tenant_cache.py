"""Tenant-resolution caching tests (B2): cache the store lookup, invalidate on change."""

from __future__ import annotations

import pytest
from django.core.cache import cache
from django.test import RequestFactory

from apps.stores.tenancy import resolve_store

pytestmark = pytest.mark.django_db


def _request(store_id):
    return RequestFactory().get("/", HTTP_X_STORE_ID=str(store_id))


def test_resolution_is_cached(make_store, django_assert_num_queries):
    store, _owner = make_store()
    first = resolve_store(_request(store.id))
    assert first.id == store.id
    # Second resolution is served from cache without touching the database.
    with django_assert_num_queries(0):
        second = resolve_store(_request(store.id))
    assert second.id == store.id


def test_store_save_invalidates_cache(make_store):
    store, _owner = make_store()
    resolve_store(_request(store.id))
    assert cache.get(f"tenant:id:{store.id}") is not None
    store.name = "Renamed Store"
    store.save(update_fields=["name", "updated_at"])
    assert cache.get(f"tenant:id:{store.id}") is None  # invalidated by the save signal


def test_settings_change_invalidates_cache(make_store):
    store, _owner = make_store()
    resolve_store(_request(store.id))
    assert cache.get(f"tenant:id:{store.id}") is not None
    store.settings.default_tax_rate = 21
    store.settings.save(update_fields=["default_tax_rate", "updated_at"])
    assert cache.get(f"tenant:id:{store.id}") is None


def test_unknown_store_is_not_cached(make_store):
    import uuid

    missing = uuid.uuid4()
    assert resolve_store(_request(missing)) is None
    assert cache.get(f"tenant:id:{missing}") is None  # negatives are not cached
