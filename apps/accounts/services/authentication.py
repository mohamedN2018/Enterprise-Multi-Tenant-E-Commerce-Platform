"""Login / logout / token-refresh orchestration."""

from __future__ import annotations

from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.exceptions import TokenError

from apps.accounts.models import SecurityEventType, User, UserDevice
from apps.accounts.repositories import (
    SecurityEventRepository,
    UserDeviceRepository,
    UserRepository,
)
from apps.accounts.services import jwt
from apps.accounts.services.security import SecurityService
from apps.core.exceptions import AuthenticationError
from apps.core.services import BaseService


class AuthenticationService(BaseService):
    def __init__(
        self,
        *,
        user_repo: UserRepository | None = None,
        device_repo: UserDeviceRepository | None = None,
        security: SecurityService | None = None,
    ) -> None:
        self.user_repo = user_repo or UserRepository()
        self.device_repo = device_repo or UserDeviceRepository()
        self.security = security or SecurityService(SecurityEventRepository())

    # --- Login ---
    def login(self, *, email: str, password: str, remember_me: bool = False, meta: dict) -> dict:
        user = self.user_repo.get_by_email(email)
        if user is None:
            self.security.log(
                SecurityEventType.LOGIN_FAILED,
                email=email,
                meta=meta,
                extra={"reason": "unknown_email"},
            )
            raise AuthenticationError("Invalid email or password.")
        if not user.check_password(password):
            # Attach the user so failed attempts are auditable per-account,
            # while keeping the client-facing message generic (no enumeration).
            self.security.log(
                SecurityEventType.LOGIN_FAILED,
                user=user,
                email=email,
                meta=meta,
                extra={"reason": "invalid_password"},
            )
            raise AuthenticationError("Invalid email or password.")

        if not user.is_active:
            self.security.log(
                SecurityEventType.LOGIN_FAILED,
                user=user,
                email=email,
                meta=meta,
                extra={"reason": "inactive"},
            )
            raise AuthenticationError("This account is inactive.", code="account_inactive")

        if settings.AUTH_SETTINGS["REQUIRE_EMAIL_VERIFICATION"] and not user.is_verified:
            self.security.log(
                SecurityEventType.LOGIN_FAILED,
                user=user,
                email=email,
                meta=meta,
                extra={"reason": "email_unverified"},
            )
            raise AuthenticationError(
                "Please verify your email address before signing in.",
                code="email_not_verified",
            )

        tokens = jwt.issue_for_user(user, remember_me=remember_me)
        device = self._register_device(user, tokens["jti"], meta)

        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        self.security.log(SecurityEventType.LOGIN_SUCCESS, user=user, meta=meta)
        return {
            "user": user,
            "access": tokens["access"],
            "refresh": tokens["refresh"],
            "device": device,
        }

    # --- Refresh ---
    def refresh(self, *, raw_refresh: str, meta: dict) -> dict:
        try:
            old_jti, user_id = jwt.rotate(raw_refresh)
        except TokenError:
            raise AuthenticationError(
                "Invalid or expired refresh token.", code="token_invalid"
            ) from None

        user = self.user_repo.get_or_none(id=user_id, is_active=True)
        if user is None:
            raise AuthenticationError("Invalid or expired refresh token.", code="token_invalid")

        tokens = jwt.issue_for_user(user)
        device = self.device_repo.get_by_jti(old_jti)
        if device is not None and device.is_active:
            device.jti = tokens["jti"]
            device.last_used_at = timezone.now()
            device.save(update_fields=["jti", "last_used_at", "updated_at"])

        self.security.log(SecurityEventType.TOKEN_REFRESH, user=user, meta=meta)
        return {"access": tokens["access"], "refresh": tokens["refresh"]}

    # --- Logout ---
    def logout(self, *, raw_refresh: str, user: User, meta: dict) -> None:
        try:
            jti = jwt.blacklist_raw(raw_refresh)
        except TokenError:
            # Already invalid/expired — treat logout as idempotent success.
            jti = None
        if jti is not None:
            device = self.device_repo.get_by_jti(jti)
            if device is not None:
                self.device_repo.deactivate(device)
        self.security.log(SecurityEventType.LOGOUT, user=user, meta=meta)

    # --- Helpers ---
    def _register_device(self, user: User, jti: str, meta: dict) -> UserDevice:
        return self.device_repo.create(
            user=user,
            jti=jti,
            device_name=meta.get("device_name", ""),
            user_agent=meta.get("user_agent", ""),
            ip_address=meta.get("ip"),
            is_active=True,
            last_used_at=timezone.now(),
        )
