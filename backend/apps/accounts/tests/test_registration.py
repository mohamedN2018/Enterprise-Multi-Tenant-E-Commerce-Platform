"""Registration endpoint tests."""

from __future__ import annotations

import pytest
from django.core import mail
from django.urls import reverse

from apps.accounts.models import OneTimeToken, SecurityEventType, TokenPurpose, User

pytestmark = pytest.mark.django_db

REGISTER_URL = reverse("v1:accounts:register")
PASSWORD = "StrongPass!2026"


def test_register_success(api_client):
    resp = api_client.post(
        REGISTER_URL,
        {"email": "new@example.com", "password": PASSWORD, "password_confirm": PASSWORD},
        format="json",
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["email"] == "new@example.com"
    assert body["data"]["is_verified"] is False

    user = User.objects.get(email="new@example.com")
    assert not user.is_verified
    assert user.check_password(PASSWORD)
    # A verification token + email were produced.
    assert OneTimeToken.objects.filter(user=user, purpose=TokenPurpose.EMAIL_VERIFICATION).exists()
    assert len(mail.outbox) == 1
    assert user.security_events.filter(event_type=SecurityEventType.REGISTER).exists()


def test_register_duplicate_email_conflict(api_client, make_user):
    make_user(email="dupe@example.com")
    resp = api_client.post(
        REGISTER_URL,
        {"email": "dupe@example.com", "password": PASSWORD, "password_confirm": PASSWORD},
        format="json",
    )
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "email_taken"


def test_register_password_mismatch(api_client):
    resp = api_client.post(
        REGISTER_URL,
        {"email": "x@example.com", "password": PASSWORD, "password_confirm": "different1!"},
        format="json",
    )
    assert resp.status_code == 400
    assert resp.json()["success"] is False


def test_register_weak_password(api_client):
    resp = api_client.post(
        REGISTER_URL,
        {"email": "x@example.com", "password": "123", "password_confirm": "123"},
        format="json",
    )
    assert resp.status_code == 400
    assert "password" in resp.json()["errors"]
