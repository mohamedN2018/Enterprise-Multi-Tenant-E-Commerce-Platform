"""Shared fixtures for inventory tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.catalog.services import CatalogService
from apps.inventory.models import Warehouse
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
    def _add(store, user, role=StoreRole.EMPLOYEE) -> StoreMembership:
        return StoreMembership.objects.create(store=store, user=user, role=role, is_active=True)

    return _add


@pytest.fixture
def store_client():
    def _make(user, store) -> APIClient:
        client = APIClient()
        client.force_authenticate(user=user)
        client.defaults["HTTP_X_STORE_ID"] = str(store.id)
        return client

    return _make


@pytest.fixture
def make_variant(db):
    counter = {"n": 0}

    def _make(store, sku: str | None = None, price: str = "10.00"):
        counter["n"] += 1
        sku = sku or f"SKU-{counter['n']}"
        product = CatalogService().create_product(store=store, data={"name": f"P-{sku}"})
        return CatalogService().create_variant(
            store=store, product=product, data={"sku": sku, "price": Decimal(price)}
        )

    return _make


@pytest.fixture
def make_warehouse(db):
    counter = {"n": 0}

    def _make(store, code: str | None = None, name: str = "Main", is_default: bool = False):
        counter["n"] += 1
        code = code or f"WH-{counter['n']}"
        return Warehouse.objects.create(store=store, name=name, code=code, is_default=is_default)

    return _make
