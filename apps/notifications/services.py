"""Notification application service: create, deliver, read, preferences."""

from __future__ import annotations

from django.utils import timezone

from apps.core.services import BaseService, atomic
from apps.notifications.models import Notification, NotificationPreference


class NotificationService(BaseService):
    @atomic
    def notify(
        self,
        *,
        store,
        recipient,
        event_type: str,
        title: str,
        body: str = "",
        data: dict | None = None,
    ) -> Notification | None:
        """Deliver a notification over the recipient's enabled channels.

        Always records an in-app entry unless the recipient has opted out; emails
        in addition when the email channel is enabled and an address is known.
        Returns the in-app ``Notification`` (or ``None`` if in-app is disabled).
        """
        preference = self.get_preference(store=store, user=recipient)
        notification = None
        if preference.in_app_enabled:
            notification = Notification.objects.create(
                store=store,
                recipient=recipient,
                event_type=event_type,
                title=title,
                body=body,
                data=data or {},
            )
        if preference.email_enabled and getattr(recipient, "email", ""):
            from apps.notifications.tasks import send_email

            send_email.delay(recipient.email, title, body or title)
        return notification

    @atomic
    def mark_read(self, *, notification: Notification) -> Notification:
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at", "updated_at"])
        return notification

    @atomic
    def mark_all_read(self, *, store, user) -> int:
        return Notification.objects.filter(store=store, recipient=user, is_read=False).update(
            is_read=True, read_at=timezone.now()
        )

    def unread_count(self, *, store, user) -> int:
        return Notification.objects.filter(store=store, recipient=user, is_read=False).count()

    # --- Preferences ---
    def get_preference(self, *, store, user) -> NotificationPreference:
        preference, _ = NotificationPreference.objects.get_or_create(store=store, user=user)
        return preference

    @atomic
    def update_preference(self, *, store, user, data: dict) -> NotificationPreference:
        preference = self.get_preference(store=store, user=user)
        for field, value in data.items():
            setattr(preference, field, value)
        preference.save()
        return preference
