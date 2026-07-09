"""Shared fixtures for shipping tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.catalog.models import ProductStatus
from apps.catalog.services import CatalogService
from apps.inventory.models import Warehouse
from apps.inventory.services import InventoryService
from apps.shipping.services import ShippingService
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

    def _make(store, *, price="100.00", stock=20, weight=None):
        counter["n"] += 1
        data = {"sku": f"SKU{counter['n']}", "price": Decimal(price)}
        if weight is not None:
            data["weight"] = Decimal(weight)
        product = CatalogService().create_product(
            store=store, data={"name": f"P{counter['n']}", "status": ProductStatus.PUBLISHED}
        )
        variant = CatalogService().create_variant(store=store, product=product, data=data)
        warehouse, _ = Warehouse.objects.get_or_create(
            store=store, code="MAIN", defaults={"name": "Main"}
        )
        InventoryService().receive(
            store=store, variant=variant, warehouse=warehouse, quantity=stock
        )
        return variant

    return _make


@pytest.fixture
def shipping_method(db):
    def _make(
        store, *, name="Standard", price="10.00", per_kg="0.00", free_over=None, countries=("DE",)
    ):
        zone = ShippingService().create_zone(
            store=store, data={"name": "Zone", "countries": list(countries)}
        )
        data = {"name": name, "price": Decimal(price), "per_kg": Decimal(per_kg)}
        if free_over is not None:
            data["free_over"] = Decimal(free_over)
        return ShippingService().add_method(store=store, zone=zone, data=data)

    return _make


@pytest.fixture
def geo_method(db):
    """A circular (map) delivery zone + a method inside it. Defaults to a 10 km
    circle centred on Cairo (30.0444, 31.2357)."""

    def _make(store, *, name="Local", price="20.00", lat="30.0444", lng="31.2357", radius_km="10"):
        zone = ShippingService().create_zone(
            store=store,
            data={
                "name": "Local circle",
                "center_lat": Decimal(lat),
                "center_lng": Decimal(lng),
                "radius_km": Decimal(radius_km),
            },
        )
        return ShippingService().add_method(
            store=store, zone=zone, data={"name": name, "price": Decimal(price)}
        )

    return _make
