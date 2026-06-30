"""Shared fixtures for search tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.catalog.models import ProductStatus
from apps.catalog.services import CatalogService
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

    def _make() -> User:
        counter["n"] += 1
        user = User.objects.create_user(email=f"user{counter['n']}@example.com", password=PASSWORD)
        user.is_verified = True
        user.save(update_fields=["is_verified"])
        return user

    return _make


@pytest.fixture
def make_store(make_user):
    def _make(name: str = "Acme Store"):
        return StoreService().create_store(owner=make_user(), data={"name": name})

    return _make


@pytest.fixture
def store_client(make_user):
    def _make(store, user=None) -> APIClient:
        client = APIClient()
        client.force_authenticate(user=user or make_user())
        client.defaults["HTTP_X_STORE_ID"] = str(store.id)
        return client

    return _make


@pytest.fixture
def make_product(db):
    counter = {"n": 0}

    def _make(
        store, *, name=None, description="", price="10.00", sku=None, status=ProductStatus.PUBLISHED
    ):
        counter["n"] += 1
        name = name or f"Product {counter['n']}"
        product = CatalogService().create_product(
            store=store, data={"name": name, "description": description, "status": status}
        )
        CatalogService().create_variant(
            store=store,
            product=product,
            data={"sku": sku or f"SKU{counter['n']}", "price": Decimal(price)},
        )
        return product

    return _make
