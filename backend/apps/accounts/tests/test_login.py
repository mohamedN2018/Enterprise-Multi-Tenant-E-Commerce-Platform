"""Login endpoint tests."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.accounts.models import SecurityEventType, UserDevice

from .conftest import PASSWORD

pytestmark = pytest.mark.django_db

LOGIN_URL = reverse("v1:accounts:login")


def test_login_success(api_client, make_user):
    user = make_user(verified=True)
    resp = api_client.post(LOGIN_URL, {"email": user.email, "password": PASSWORD}, format="json")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["user"]["email"] == user.email
    assert data["tokens"]["access"]
    assert data["tokens"]["refresh"]
    # A device/session and a success event were recorded.
    assert UserDevice.objects.filter(user=user, is_active=True).count() == 1
    assert user.security_events.filter(event_type=SecurityEventType.LOGIN_SUCCESS).exists()


def test_login_wrong_password(api_client, make_user):
    user = make_user(verified=True)
    resp = api_client.post(
        LOGIN_URL, {"email": user.email, "password": "WrongPass!2026"}, format="json"
    )
    assert resp.status_code == 401
    assert user.security_events.filter(event_type=SecurityEventType.LOGIN_FAILED).exists()


def test_login_unknown_email(api_client):
    resp = api_client.post(
        LOGIN_URL, {"email": "ghost@example.com", "password": PASSWORD}, format="json"
    )
    assert resp.status_code == 401


def test_login_unverified_blocked(api_client, make_user):
    user = make_user(email="unverified@example.com", verified=False)
    resp = api_client.post(LOGIN_URL, {"email": user.email, "password": PASSWORD}, format="json")
    assert resp.status_code == 401
    assert resp.json()["error_code"] == "email_not_verified"


def test_login_inactive_blocked(api_client, make_user):
    user = make_user(email="inactive@example.com", verified=True, is_active=False)
    resp = api_client.post(LOGIN_URL, {"email": user.email, "password": PASSWORD}, format="json")
    assert resp.status_code == 401
    assert resp.json()["error_code"] == "account_inactive"
