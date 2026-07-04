"""User registration + email verification services."""

from __future__ import annotations

from django.conf import settings

from apps.accounts import tasks
from apps.accounts.models import SecurityEventType, TokenPurpose, User
from apps.accounts.repositories import OneTimeTokenRepository, UserRepository
from apps.accounts.services.security import SecurityService
from apps.accounts.tokens import generate_raw_token
from apps.core.exceptions import ValidationError
from apps.core.services import BaseService, atomic


class RegistrationService(BaseService):
    def __init__(
        self,
        *,
        user_repo: UserRepository | None = None,
        token_repo: OneTimeTokenRepository | None = None,
        security: SecurityService | None = None,
    ) -> None:
        self.user_repo = user_repo or UserRepository()
        self.token_repo = token_repo or OneTimeTokenRepository()
        self.security = security or SecurityService()

    @atomic
    def register(self, *, email: str, password: str, meta: dict | None = None) -> User | None:
        if self.user_repo.email_exists(email):
            # Enumeration-safe: never reveal that the address is taken. Log the
            # attempt and bail — the endpoint responds identically to a fresh
            # signup, so an attacker can't distinguish existing from new emails.
            self.security.log(
                SecurityEventType.REGISTER,
                email=email,
                meta=meta,
                extra={"reason": "duplicate_email"},
            )
            return None
        user = self.user_repo.create_user(
            email=email, password=password, is_active=True, is_verified=False
        )
        self._send_verification(user)
        self.security.log(SecurityEventType.REGISTER, user=user, meta=meta)
        return user

    def _send_verification(self, user: User) -> None:
        raw_token = generate_raw_token()
        self.token_repo.issue(
            user=user,
            purpose=TokenPurpose.EMAIL_VERIFICATION,
            raw_token=raw_token,
            ttl_hours=settings.AUTH_SETTINGS["EMAIL_VERIFICATION_TTL_HOURS"],
        )
        tasks.send_verification_email.delay(user.email, raw_token)


class EmailVerificationService(BaseService):
    def __init__(
        self,
        *,
        user_repo: UserRepository | None = None,
        token_repo: OneTimeTokenRepository | None = None,
        security: SecurityService | None = None,
    ) -> None:
        self.user_repo = user_repo or UserRepository()
        self.token_repo = token_repo or OneTimeTokenRepository()
        self.security = security or SecurityService()

    @atomic
    def verify(self, *, raw_token: str, meta: dict | None = None) -> User:
        token = self.token_repo.get_valid(
            purpose=TokenPurpose.EMAIL_VERIFICATION, raw_token=raw_token
        )
        if token is None:
            raise ValidationError(
                "This verification link is invalid or has expired.",
                code="invalid_token",
            )
        token.consume()
        user = token.user
        if not user.is_verified:
            user.mark_verified()
        self.security.log(SecurityEventType.EMAIL_VERIFIED, user=user, meta=meta)
        return user

    def resend(self, *, email: str) -> None:
        """Re-issue a verification token. Silent on unknown/verified accounts
        to avoid account enumeration."""
        user = self.user_repo.get_by_email(email)
        if user is None or user.is_verified or not user.is_active:
            return
        self.token_repo.invalidate_outstanding(user=user, purpose=TokenPurpose.EMAIL_VERIFICATION)
        raw_token = generate_raw_token()
        self.token_repo.issue(
            user=user,
            purpose=TokenPurpose.EMAIL_VERIFICATION,
            raw_token=raw_token,
            ttl_hours=settings.AUTH_SETTINGS["EMAIL_VERIFICATION_TTL_HOURS"],
        )
        tasks.send_verification_email.delay(user.email, raw_token)
