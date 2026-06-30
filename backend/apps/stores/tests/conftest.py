"""Shared fixtures for stores tests."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.stores.services import StoreService

PASSWORD = "StrongPass!2026"


@pytest.fixture(autouse=True)
def _isolate_cache():
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def make_user(db):
    counter = {"n": 0}

    def _make(email: str | None = None, **extra) -> User:
        if email is None:
            counter["n"] += 1
            email = f"user{counter['n']}@example.com"
        user = User.objects.create_user(email=email, password=PASSWORD, **extra)
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
def client_for(api_client):
    def _as(user) -> APIClient:
        api_client.force_authenticate(user=user)
        return api_client

    return _as
