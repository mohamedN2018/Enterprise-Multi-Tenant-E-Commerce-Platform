"""Password reset & change services."""

from __future__ import annotations

from django.conf import settings

from apps.accounts import tasks
from apps.accounts.models import SecurityEventType, TokenPurpose, User
from apps.accounts.repositories import (
    OneTimeTokenRepository,
    UserDeviceRepository,
    UserRepository,
)
from apps.accounts.services import jwt
from apps.accounts.services.security import SecurityService
from apps.accounts.tokens import generate_raw_token
from apps.core.exceptions import ValidationError
from apps.core.services import BaseService, atomic


class PasswordService(BaseService):
    def __init__(
        self,
        *,
        user_repo: UserRepository | None = None,
        token_repo: OneTimeTokenRepository | None = None,
        device_repo: UserDeviceRepository | None = None,
        security: SecurityService | None = None,
    ) -> None:
        self.user_repo = user_repo or UserRepository()
        self.token_repo = token_repo or OneTimeTokenRepository()
        self.device_repo = device_repo or UserDeviceRepository()
        self.security = security or SecurityService()

    def request_reset(self, *, email: str, meta: dict) -> None:
        """Issue a reset token. Always succeeds silently (no enumeration)."""
        user = self.user_repo.get_by_email(email)
        self.security.log(
            SecurityEventType.PASSWORD_RESET_REQUESTED, user=user, email=email, meta=meta
        )
        if user is None or not user.is_active:
            return
        self.token_repo.invalidate_outstanding(user=user, purpose=TokenPurpose.PASSWORD_RESET)
        raw_token = generate_raw_token()
        self.token_repo.issue(
            user=user,
            purpose=TokenPurpose.PASSWORD_RESET,
            raw_token=raw_token,
            ttl_hours=settings.AUTH_SETTINGS["PASSWORD_RESET_TTL_HOURS"],
        )
        tasks.send_password_reset_email.delay(user.email, raw_token)

    @atomic
    def confirm_reset(self, *, raw_token: str, new_password: str, meta: dict) -> User:
        token = self.token_repo.get_valid(purpose=TokenPurpose.PASSWORD_RESET, raw_token=raw_token)
        if token is None:
            raise ValidationError(
                "This reset link is invalid or has expired.", code="invalid_token"
            )
        user = token.user
        user.set_password(new_password)
        user.save(update_fields=["password", "updated_at"])
        token.consume()
        self._revoke_all_sessions(user)
        self.security.log(SecurityEventType.PASSWORD_RESET, user=user, meta=meta)
        return user

    @atomic
    def change_password(
        self, *, user: User, current_password: str, new_password: str, meta: dict
    ) -> None:
        if not user.check_password(current_password):
            raise ValidationError(
                "Your current password is incorrect.",
                code="invalid_password",
                errors={"current_password": ["Incorrect password."]},
            )
        user.set_password(new_password)
        user.save(update_fields=["password", "updated_at"])
        # Force re-authentication everywhere after a credential change.
        self._revoke_all_sessions(user)
        self.security.log(SecurityEventType.PASSWORD_CHANGED, user=user, meta=meta)

    def _revoke_all_sessions(self, user: User) -> None:
        for device in self.device_repo.active_for_user(user):
            jwt.blacklist_jti(device.jti)
            device.is_active = False
            device.save(update_fields=["is_active", "updated_at"])
