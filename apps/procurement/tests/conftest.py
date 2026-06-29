"""Shared fixtures for procurement tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.catalog.services import CatalogService
from apps.inventory.models import Warehouse
from apps.procurement.models import Supplier
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
        owner = make_user()
        return StoreService().create_store(owner=owner, data={"name": name}), owner

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

    def _make(store, price="10.00"):
        counter["n"] += 1
        product = CatalogService().create_product(store=store, data={"name": f"P{counter['n']}"})
        return CatalogService().create_variant(
            store=store,
            product=product,
            data={"sku": f"SKU{counter['n']}", "price": Decimal(price)},
        )

    return _make


@pytest.fixture
def make_warehouse(db):
    counter = {"n": 0}

    def _make(store, is_default: bool = False):
        counter["n"] += 1
        return Warehouse.objects.create(
            store=store, name=f"WH{counter['n']}", code=f"WH-{counter['n']}", is_default=is_default
        )

    return _make


@pytest.fixture
def make_supplier(db):
    counter = {"n": 0}

    def _make(store, name: str = "Vendor"):
        counter["n"] += 1
        return Supplier.objects.create(
            store=store, name=f"{name}{counter['n']}", code=f"sup-{counter['n']}"
        )

    return _make
