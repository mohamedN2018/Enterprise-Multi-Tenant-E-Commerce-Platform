"""Shared fixtures for rewards tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.catalog.models import ProductStatus
from apps.catalog.services import CatalogService
from apps.inventory.models import Warehouse
from apps.inventory.services import InventoryService
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
        return StoreService().create_store(owner=make_user(), data={"name": name}), None

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

    def _make(store, *, price="60.00", stock=10):
        counter["n"] += 1
        product = CatalogService().create_product(
            store=store, data={"name": f"P{counter['n']}", "status": ProductStatus.PUBLISHED}
        )
        variant = CatalogService().create_variant(
            store=store,
            product=product,
            data={"sku": f"SKU{counter['n']}", "price": Decimal(price)},
        )
        warehouse, _ = Warehouse.objects.get_or_create(
            store=store, code="MAIN", defaults={"name": "Main"}
        )
        InventoryService().receive(
            store=store, variant=variant, warehouse=warehouse, quantity=stock
        )
        return variant

    return _make
