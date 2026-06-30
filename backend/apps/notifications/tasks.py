"""Celery tasks for notifications (async email delivery).

Runs eagerly in tests (``CELERY_TASK_ALWAYS_EAGER``); enqueued to a worker in
production so request/checkout latency is unaffected by the mail round-trip.
"""

from __future__ import annotations

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task(
    name="notifications.send_email",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def send_email(recipient: str, subject: str, message: str) -> None:
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        fail_silently=False,
    )
