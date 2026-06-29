"""Shared fixtures for ordering (cart/checkout) tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.catalog.models import ProductStatus
from apps.catalog.services import CatalogService
from apps.inventory.models import Warehouse
from apps.inventory.services import InventoryService
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
        return StoreService().create_store(owner=owner, data={"name": name})

    return _make


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

    def _make(store, *, price: str = "10.00", published: bool = True):
        counter["n"] += 1
        status = ProductStatus.PUBLISHED if published else ProductStatus.DRAFT
        product = CatalogService().create_product(
            store=store, data={"name": f"Product {counter['n']}", "status": status}
        )
        return CatalogService().create_variant(
            store=store,
            product=product,
            data={"sku": f"SKU-{counter['n']}", "price": Decimal(price)},
        )

    return _make


@pytest.fixture
def seed_stock(db):
    def _seed(store, variant, quantity: int, code: str = "MAIN"):
        warehouse, _ = Warehouse.objects.get_or_create(
            store=store, code=code, defaults={"name": "Main"}
        )
        InventoryService().receive(
            store=store, variant=variant, warehouse=warehouse, quantity=quantity
        )
        return warehouse

    return _seed
