"""Celery tasks for the accounts app."""

from __future__ import annotations

from celery import shared_task

from apps.accounts import emails


@shared_task(
    name="accounts.send_verification_email",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def send_verification_email(email: str, raw_token: str) -> None:
    emails.send_verification_email(email, raw_token)


@shared_task(
    name="accounts.send_password_reset_email",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def send_password_reset_email(email: str, raw_token: str) -> None:
    emails.send_password_reset_email(email, raw_token)
