"""Email verification endpoint tests."""

from __future__ import annotations

import pytest
from django.core import mail
from django.urls import reverse

from apps.accounts.models import OneTimeToken, TokenPurpose

from .conftest import PASSWORD, extract_token_from_email

pytestmark = pytest.mark.django_db

REGISTER_URL = reverse("v1:accounts:register")
VERIFY_URL = reverse("v1:accounts:verify-email")
RESEND_URL = reverse("v1:accounts:resend-verification")


def _register(api_client, email="verify@example.com"):
    api_client.post(
        REGISTER_URL,
        {"email": email, "password": PASSWORD, "password_confirm": PASSWORD},
        format="json",
    )
    return extract_token_from_email(mail.outbox[-1].body)


def test_verify_success(api_client, django_user_model):
    token = _register(api_client)
    resp = api_client.post(VERIFY_URL, {"token": token}, format="json")
    assert resp.status_code == 200
    assert resp.json()["data"]["is_verified"] is True

    user = django_user_model.objects.get(email="verify@example.com")
    assert user.is_verified
    assert user.verified_at is not None
    # Token is now consumed and cannot be reused.
    assert (
        OneTimeToken.all_objects.get(purpose=TokenPurpose.EMAIL_VERIFICATION, user=user).used_at
        is not None
    )

    replay = api_client.post(VERIFY_URL, {"token": token}, format="json")
    assert replay.status_code == 400


def test_verify_invalid_token(api_client):
    resp = api_client.post(VERIFY_URL, {"token": "nonsense"}, format="json")
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "invalid_token"


def test_resend_is_silent_for_unknown_email(api_client):
    resp = api_client.post(RESEND_URL, {"email": "ghost@example.com"}, format="json")
    assert resp.status_code == 200
    assert len(mail.outbox) == 0


def test_resend_issues_new_token(api_client):
    _register(api_client, email="resend@example.com")
    outbox_before = len(mail.outbox)
    resp = api_client.post(RESEND_URL, {"email": "resend@example.com"}, format="json")
    assert resp.status_code == 200
    assert len(mail.outbox) == outbox_before + 1
