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
    # Enumeration-safe: a generic 202 with no user data.
    assert resp.status_code == 202
    body = resp.json()
    assert body["success"] is True
    assert body["data"] is None

    user = User.objects.get(email="new@example.com")
    assert not user.is_verified
    assert user.check_password(PASSWORD)
    # A verification token + email were produced.
    assert OneTimeToken.objects.filter(user=user, purpose=TokenPurpose.EMAIL_VERIFICATION).exists()
    assert len(mail.outbox) == 1
    assert user.security_events.filter(event_type=SecurityEventType.REGISTER).exists()


def test_register_duplicate_email_is_not_enumerable(api_client, make_user):
    """A taken email must return the SAME response as a fresh signup — no 409,
    no leak — and must not create a second account or send an email."""
    make_user(email="dupe@example.com")
    resp = api_client.post(
        REGISTER_URL,
        {"email": "dupe@example.com", "password": PASSWORD, "password_confirm": PASSWORD},
        format="json",
    )
    assert resp.status_code == 202
    body = resp.json()
    assert body["success"] is True
    assert body["data"] is None
    assert "email_taken" not in resp.content.decode()
    # No duplicate user, no verification email sent for the existing account.
    assert User.objects.filter(email="dupe@example.com").count() == 1
    assert len(mail.outbox) == 0


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
