"""Tenant-resolution tests + the tenant-aware manager scoping."""

from __future__ import annotations

import pytest
from django.test import RequestFactory

from apps.core import tenancy
from apps.stores.tenancy import resolve_store

pytestmark = pytest.mark.django_db


def test_resolve_by_slug_header(make_store):
    store, _owner = make_store(name="Acme")
    request = RequestFactory().get("/", HTTP_X_STORE_SLUG=store.slug)
    assert resolve_store(request).id == store.id


def test_resolve_by_id_header(make_store):
    store, _owner = make_store()
    request = RequestFactory().get("/", HTTP_X_STORE_ID=str(store.id))
    assert resolve_store(request).id == store.id


def test_resolve_returns_none_without_hint():
    request = RequestFactory().get("/")
    assert resolve_store(request) is None


def test_resolve_returns_none_for_unknown_slug(db):
    request = RequestFactory().get("/", HTTP_X_STORE_SLUG="does-not-exist")
    assert resolve_store(request) is None


def test_resolve_handles_malformed_id(db):
    request = RequestFactory().get("/", HTTP_X_STORE_ID="not-a-uuid")
    assert resolve_store(request) is None


def test_resolve_ignores_soft_deleted_store(make_store):
    store, _owner = make_store()
    store.delete()  # soft delete
    request = RequestFactory().get("/", HTTP_X_STORE_SLUG=store.slug)
    assert resolve_store(request) is None


def test_tenant_context_is_clean_outside_request():
    # Nothing bound by default.
    assert tenancy.get_current_store() is None
