"""Device management & profile (me) tests."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.accounts.models import UserDevice
from apps.accounts.services import AuthenticationService

from .conftest import PASSWORD

pytestmark = pytest.mark.django_db

ME_URL = reverse("v1:accounts:me")
DEVICES_URL = reverse("v1:accounts:device-list")
REVOKE_ALL_URL = reverse("v1:accounts:device-revoke-all")
REFRESH_URL = reverse("v1:accounts:token-refresh")


def _login(user, ua="pytest"):
    return AuthenticationService().login(
        email=user.email,
        password=PASSWORD,
        remember_me=False,
        meta={"ip": "127.0.0.1", "user_agent": ua, "device_name": ua},
    )


def test_me_returns_profile(auth_client):
    client, user, _ = auth_client()
    resp = client.get(ME_URL)
    assert resp.status_code == 200
    assert resp.json()["data"]["email"] == user.email


def test_me_requires_auth(api_client):
    assert api_client.get(ME_URL).status_code == 401


def test_device_list_shows_active_sessions(api_client, make_user):
    user = make_user(verified=True)
    first = _login(user, ua="device-a")
    _login(user, ua="device-b")

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {first['access']}")
    resp = api_client.get(DEVICES_URL)
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["pagination"]["count"] == 2
    assert len(body["data"]) == 2


def test_revoke_single_device(api_client, make_user):
    user = make_user(verified=True)
    first = _login(user, ua="keep")
    second = _login(user, ua="revoke")
    target = second["device"]  # the device created for the second session

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {first['access']}")
    url = reverse("v1:accounts:device-revoke", kwargs={"device_id": target.id})
    resp = api_client.delete(url)
    assert resp.status_code == 200

    target.refresh_from_db()
    assert target.is_active is False
    # The revoked session's refresh token is blacklisted.
    api_client.credentials()
    replay = api_client.post(REFRESH_URL, {"refresh": second["refresh"]}, format="json")
    assert replay.status_code == 401


def test_revoke_all_devices(api_client, make_user):
    user = make_user(verified=True)
    first = _login(user, ua="a")
    _login(user, ua="b")

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {first['access']}")
    resp = api_client.post(REVOKE_ALL_URL)
    assert resp.status_code == 200
    assert resp.json()["data"]["revoked"] == 2
    assert UserDevice.objects.filter(user=user, is_active=True).count() == 0
