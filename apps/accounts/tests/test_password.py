"""Password reset & change tests."""

from __future__ import annotations

import pytest
from django.core import mail
from django.urls import reverse

from apps.accounts.models import OneTimeToken, SecurityEventType, TokenPurpose, UserDevice

from .conftest import PASSWORD, extract_token_from_email

pytestmark = pytest.mark.django_db

LOGIN_URL = reverse("v1:accounts:login")
RESET_URL = reverse("v1:accounts:password-reset")
RESET_CONFIRM_URL = reverse("v1:accounts:password-reset-confirm")
CHANGE_URL = reverse("v1:accounts:password-change")

NEW_PASSWORD = "BrandNewPass!2026"


def test_reset_request_is_silent_for_unknown_email(api_client):
    resp = api_client.post(RESET_URL, {"email": "ghost@example.com"}, format="json")
    assert resp.status_code == 200
    assert len(mail.outbox) == 0


def test_reset_request_issues_token(api_client, make_user):
    user = make_user(verified=True)
    resp = api_client.post(RESET_URL, {"email": user.email}, format="json")
    assert resp.status_code == 200
    assert OneTimeToken.objects.filter(user=user, purpose=TokenPurpose.PASSWORD_RESET).exists()
    assert len(mail.outbox) == 1


def test_reset_confirm_changes_password(api_client, make_user):
    user = make_user(verified=True)
    api_client.post(RESET_URL, {"email": user.email}, format="json")
    token = extract_token_from_email(mail.outbox[-1].body)

    resp = api_client.post(
        RESET_CONFIRM_URL,
        {"token": token, "new_password": NEW_PASSWORD, "new_password_confirm": NEW_PASSWORD},
        format="json",
    )
    assert resp.status_code == 200

    user.refresh_from_db()
    assert user.check_password(NEW_PASSWORD)
    assert user.security_events.filter(event_type=SecurityEventType.PASSWORD_RESET).exists()
    # New password works at login.
    login = api_client.post(
        LOGIN_URL, {"email": user.email, "password": NEW_PASSWORD}, format="json"
    )
    assert login.status_code == 200


def test_reset_confirm_invalid_token(api_client):
    resp = api_client.post(
        RESET_CONFIRM_URL,
        {"token": "bad", "new_password": NEW_PASSWORD, "new_password_confirm": NEW_PASSWORD},
        format="json",
    )
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "invalid_token"


def test_change_password_success_revokes_sessions(api_client, auth_client):
    client, user, _refresh = auth_client()
    resp = client.post(
        CHANGE_URL,
        {
            "current_password": PASSWORD,
            "new_password": NEW_PASSWORD,
            "new_password_confirm": NEW_PASSWORD,
        },
        format="json",
    )
    assert resp.status_code == 200
    user.refresh_from_db()
    assert user.check_password(NEW_PASSWORD)
    # All sessions revoked after a credential change.
    assert UserDevice.objects.filter(user=user, is_active=True).count() == 0


def test_change_password_wrong_current(api_client, auth_client):
    client, _user, _refresh = auth_client()
    resp = client.post(
        CHANGE_URL,
        {
            "current_password": "WrongCurrent!2026",
            "new_password": NEW_PASSWORD,
            "new_password_confirm": NEW_PASSWORD,
        },
        format="json",
    )
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "invalid_password"
