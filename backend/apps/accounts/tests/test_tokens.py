"""Refresh-token rotation & logout (blacklist) tests."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.accounts.models import UserDevice

from .conftest import PASSWORD

pytestmark = pytest.mark.django_db

LOGIN_URL = reverse("v1:accounts:login")
REFRESH_URL = reverse("v1:accounts:token-refresh")
LOGOUT_URL = reverse("v1:accounts:logout")


def _login(api_client, user):
    resp = api_client.post(LOGIN_URL, {"email": user.email, "password": PASSWORD}, format="json")
    return resp.json()["data"]["tokens"]


def test_refresh_rotates_and_blacklists_old(api_client, make_user):
    user = make_user(verified=True)
    tokens = _login(api_client, user)

    resp = api_client.post(REFRESH_URL, {"refresh": tokens["refresh"]}, format="json")
    assert resp.status_code == 200
    new = resp.json()["data"]
    assert new["access"] and new["refresh"]
    assert new["refresh"] != tokens["refresh"]

    # The old (rotated) refresh token is now blacklisted.
    replay = api_client.post(REFRESH_URL, {"refresh": tokens["refresh"]}, format="json")
    assert replay.status_code == 401


def test_refresh_updates_device_jti(api_client, make_user):
    user = make_user(verified=True)
    tokens = _login(api_client, user)
    original_jti = UserDevice.objects.get(user=user).jti

    api_client.post(REFRESH_URL, {"refresh": tokens["refresh"]}, format="json")
    device = UserDevice.objects.get(user=user)
    assert device.is_active
    assert device.jti != original_jti


def test_logout_blacklists_refresh_and_deactivates_device(api_client, make_user):
    user = make_user(verified=True)
    tokens = _login(api_client, user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    resp = api_client.post(LOGOUT_URL, {"refresh": tokens["refresh"]}, format="json")
    assert resp.status_code == 200

    # Device deactivated; refresh no longer usable.
    assert UserDevice.objects.filter(user=user, is_active=True).count() == 0
    api_client.credentials()
    replay = api_client.post(REFRESH_URL, {"refresh": tokens["refresh"]}, format="json")
    assert replay.status_code == 401


def test_logout_requires_authentication(api_client, make_user):
    user = make_user(verified=True)
    tokens = _login(api_client, user)
    api_client.credentials()  # no auth header
    resp = api_client.post(LOGOUT_URL, {"refresh": tokens["refresh"]}, format="json")
    assert resp.status_code == 401
