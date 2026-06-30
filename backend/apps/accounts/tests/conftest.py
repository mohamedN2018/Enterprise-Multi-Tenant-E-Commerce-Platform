"""Shared fixtures & helpers for accounts tests."""

from __future__ import annotations

import re

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User

PASSWORD = "StrongPass!2026"


@pytest.fixture(autouse=True)
def _isolate_cache():
    """Reset the cache between tests so DRF throttle state never leaks."""
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def make_user(db):
    def _make(
        email: str = "user@example.com",
        password: str = PASSWORD,
        *,
        verified: bool = True,
        **extra,
    ) -> User:
        user = User.objects.create_user(email=email, password=password, **extra)
        if verified:
            user.is_verified = True
            user.save(update_fields=["is_verified"])
        return user

    return _make


@pytest.fixture
def auth_client(api_client, make_user):
    """An APIClient authenticated as a freshly logged-in user via JWT.

    Returns ``(client, user, refresh_token)``.
    """

    def _login(user=None):
        user = user or make_user()
        from apps.accounts.services import AuthenticationService

        result = AuthenticationService().login(
            email=user.email,
            password=PASSWORD,
            remember_me=False,
            meta={"ip": "127.0.0.1", "user_agent": "pytest", "device_name": "pytest"},
        )
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {result['access']}")
        return api_client, user, result["refresh"]

    return _login


def extract_token_from_email(body: str) -> str:
    match = re.search(r"token=([A-Za-z0-9_\-]+)", body)
    assert match, f"No token found in email body:\n{body}"
    return match.group(1)
