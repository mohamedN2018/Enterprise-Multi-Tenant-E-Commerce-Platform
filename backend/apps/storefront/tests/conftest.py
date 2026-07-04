"""Shared fixtures for storefront tests."""

from __future__ import annotations

import pytest
from django.utils import timezone

from apps.accounts.models import User
from apps.catalog.models import Product, ProductStatus
from apps.stores.models import StoreStatus
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
def active_store(make_user):
    """A published (ACTIVE) store the storefront will surface."""

    def _make(name: str = "متجر", name_en: str = "Shop"):
        owner = make_user()
        store = StoreService().create_store(owner=owner, data={"name": name})
        store.name_en = name_en
        store.status = StoreStatus.ACTIVE
        store.save(update_fields=["name_en", "status"])
        return store

    return _make


@pytest.fixture
def make_product(db):
    def _make(store, *, name, name_en, description, description_en, slug="prod"):
        return Product.objects.create(
            store=store,
            name=name,
            name_en=name_en,
            slug=slug,
            description=description,
            description_en=description_en,
            status=ProductStatus.PUBLISHED,
            is_active=True,
            published_at=timezone.now(),
        )

    return _make
