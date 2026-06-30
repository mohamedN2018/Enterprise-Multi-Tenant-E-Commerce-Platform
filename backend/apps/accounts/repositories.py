"""Data-access repositories for the accounts app."""

from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from apps.accounts.models import (
    OneTimeToken,
    SecurityEvent,
    User,
    UserDevice,
)
from apps.accounts.tokens import hash_token
from apps.core.repositories import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_email(self, email: str) -> User | None:
        return self.get_or_none(email=User.objects.normalize_email(email))

    def email_exists(self, email: str) -> bool:
        return self.exists(email=User.objects.normalize_email(email))

    def create_user(self, *, email: str, password: str, **extra) -> User:
        # Routes through the manager so the password is hashed correctly.
        return User.objects.create_user(email=email, password=password, **extra)


class OneTimeTokenRepository(BaseRepository[OneTimeToken]):
    model = OneTimeToken

    def issue(self, *, user: User, purpose: str, raw_token: str, ttl_hours: int) -> OneTimeToken:
        return self.create(
            user=user,
            purpose=purpose,
            token_hash=hash_token(raw_token),
            expires_at=timezone.now() + timedelta(hours=ttl_hours),
        )

    def get_valid(self, *, purpose: str, raw_token: str) -> OneTimeToken | None:
        return (
            OneTimeToken.objects.valid()
            .filter(purpose=purpose, token_hash=hash_token(raw_token))
            .select_related("user")
            .first()
        )

    def invalidate_outstanding(self, *, user: User, purpose: str) -> int:
        """Soft-delete any unused tokens of this purpose for the user."""
        return OneTimeToken.objects.filter(
            user=user, purpose=purpose, used_at__isnull=True
        ).delete()


class UserDeviceRepository(BaseRepository[UserDevice]):
    model = UserDevice

    def get_by_jti(self, jti: str) -> UserDevice | None:
        return self.get_or_none(jti=jti)

    def active_for_user(self, user: User):
        return UserDevice.objects.filter(user=user, is_active=True)

    def deactivate(self, device: UserDevice) -> None:
        device.is_active = False
        device.save(update_fields=["is_active", "updated_at"])


class SecurityEventRepository(BaseRepository[SecurityEvent]):
    model = SecurityEvent

    def record(
        self,
        *,
        event_type: str,
        user: User | None = None,
        email: str = "",
        ip_address: str | None = None,
        user_agent: str = "",
        metadata: dict | None = None,
    ) -> SecurityEvent:
        return SecurityEvent.objects.create(
            event_type=event_type,
            user=user,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {},
        )
