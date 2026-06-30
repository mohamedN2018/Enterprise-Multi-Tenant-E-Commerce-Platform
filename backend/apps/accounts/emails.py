"""Email composition & delivery for auth flows.

These functions run synchronously; they are normally invoked from Celery tasks
(see :mod:`apps.accounts.tasks`) so request latency is unaffected.
"""

from __future__ import annotations

from django.conf import settings
from django.core.mail import send_mail


def _frontend_url(path: str, raw_token: str) -> str:
    base = settings.FRONTEND_URL.rstrip("/")
    return f"{base}{path}?token={raw_token}"


def send_verification_email(email: str, raw_token: str) -> None:
    url = _frontend_url(settings.FRONTEND_EMAIL_VERIFICATION_PATH, raw_token)
    send_mail(
        subject="Verify your email address",
        message=(
            "Welcome! Please verify your email address by visiting the link below:\n\n"
            f"{url}\n\n"
            "If you did not create an account, you can safely ignore this email."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


def send_password_reset_email(email: str, raw_token: str) -> None:
    url = _frontend_url(settings.FRONTEND_PASSWORD_RESET_PATH, raw_token)
    send_mail(
        subject="Reset your password",
        message=(
            "We received a request to reset your password. Use the link below:\n\n"
            f"{url}\n\n"
            "If you did not request this, you can safely ignore this email."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
