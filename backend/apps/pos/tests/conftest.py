"""Shared fixtures for POS (cashier) tests."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.catalog.models import Product
from apps.catalog.services import CatalogService
from apps.stores.models import StoreMembership, StoreRole
from apps.stores.services import StoreService

PASSWORD = "StrongPass!2026"


@pytest.fixture(autouse=True)
def _isolate_cache():
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def make_user(db):
    counter = {"n": 0}

    def _make(email: str | None = None) -> User:
        if email is None:
            counter["n"] += 1
            email = f"user{counter['n']}@example.com"
        user = User.objects.create_user(email=email, password=PASSWORD)
        user.is_verified = True
        user.save(update_fields=["is_verified"])
        return user

    return _make


@pytest.fixture
def make_store(make_user):
    def _make(owner=None, name: str = "Acme Store"):
        owner = owner or make_user()
        store = StoreService().create_store(owner=owner, data={"name": name})
        return store, owner

    return _make


@pytest.fixture
def add_member(db):
    def _add(store, user, role=StoreRole.EMPLOYEE, permissions=None) -> StoreMembership:
        return StoreMembership.objects.create(
            store=store, user=user, role=role, is_active=True, permissions=permissions or []
        )

    return _add


@pytest.fixture
def store_client():
    """APIClient authenticated as ``user`` with the store-context header set."""

    def _make(user, store) -> APIClient:
        client = APIClient()
        client.force_authenticate(user=user)
        client.defaults["HTTP_X_STORE_ID"] = str(store.id)
        return client

    return _make


@pytest.fixture
def make_variant(db):
    """A published product with a default variant carrying ``stock`` on-hand."""

    def _make(store, *, sku, price="50.00", stock=10, track=True):
        product = CatalogService().create_product(store=store, data={"name": f"P-{sku}"})
        variant = CatalogService().create_variant(
            store=store,
            product=product,
            data={
                "sku": sku,
                "price": price,
                "stock_quantity": stock,
                "track_inventory": track,
                "is_default": True,
            },
        )
        return product, variant

    return _make
