"""Accounts domain models.

* ``User``           — platform-wide authentication identity (email login, UUID PK).
* ``OneTimeToken``   — single-use, hashed tokens for email verification & password reset.
* ``UserDevice``     — one record per active refresh-token session (device management).
* ``SecurityEvent``  — append-only audit log of security-relevant actions.

Per the chosen topology (isolated, Shopify-style stores), *customer* identity is
store-scoped and modelled separately in a later feature — it does not change
``AUTH_USER_MODEL``.
"""

from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.accounts.managers import OneTimeTokenManager, UserManager
from apps.core.managers import AllObjectsManager
from apps.core.models import BaseModel
from apps.core.models.base import TimeStampedModel, UUIDPrimaryKeyModel


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    email = models.EmailField(unique=True, db_index=True, verbose_name="email address")
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive accounts cannot authenticate.",
    )
    is_staff = models.BooleanField(
        default=False,
        help_text="Designates access to the Django admin site.",
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether the email address has been verified.",
    )
    verified_at = models.DateTimeField(null=True, blank=True, editable=False)
    # Forward hook for 2FA / passkey enrolment (full implementation is a later feature).
    two_factor_enabled = models.BooleanField(default=False)

    objects = UserManager()
    all_objects = AllObjectsManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta(BaseModel.Meta):
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.email

    def clean(self) -> None:
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def mark_verified(self) -> None:
        self.is_verified = True
        self.verified_at = timezone.now()
        self.save(update_fields=["is_verified", "verified_at", "updated_at"])


class TokenPurpose(models.TextChoices):
    EMAIL_VERIFICATION = "email_verification", "Email verification"
    PASSWORD_RESET = "password_reset", "Password reset"


class OneTimeToken(BaseModel):
    """Single-use token. Only the SHA-256 hash of the raw token is stored."""

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="one_time_tokens",
    )
    purpose = models.CharField(
        max_length=32,
        choices=TokenPurpose.choices,
        db_index=True,
    )
    token_hash = models.CharField(max_length=64, db_index=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    objects = OneTimeTokenManager()
    all_objects = AllObjectsManager()

    class Meta(BaseModel.Meta):
        verbose_name = "One-time token"
        verbose_name_plural = "One-time tokens"
        indexes = [
            models.Index(fields=["purpose", "token_hash"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_purpose_display()} for {self.user_id}"

    @property
    def is_expired(self) -> bool:
        return self.expires_at <= timezone.now()

    @property
    def is_used(self) -> bool:
        return self.used_at is not None

    def is_valid(self) -> bool:
        return not self.is_deleted and not self.is_used and not self.is_expired

    def consume(self) -> None:
        self.used_at = timezone.now()
        self.save(update_fields=["used_at", "updated_at"])


class UserDevice(BaseModel):
    """An active session/device, keyed by the current refresh-token ``jti``."""

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="devices",
    )
    jti = models.CharField(max_length=255, db_index=True)
    device_name = models.CharField(max_length=255, blank=True)
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    last_used_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta(BaseModel.Meta):
        verbose_name = "User device"
        verbose_name_plural = "User devices"
        ordering = ("-last_used_at",)
        indexes = [
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self) -> str:
        return self.device_name or f"device:{self.jti[:8]}"


class SecurityEventType(models.TextChoices):
    REGISTER = "register", "Registration"
    EMAIL_VERIFIED = "email_verified", "Email verified"
    LOGIN_SUCCESS = "login_success", "Login success"
    LOGIN_FAILED = "login_failed", "Login failed"
    LOGOUT = "logout", "Logout"
    TOKEN_REFRESH = "token_refresh", "Token refresh"
    PASSWORD_RESET_REQUESTED = "password_reset_requested", "Password reset requested"
    PASSWORD_RESET = "password_reset", "Password reset"
    PASSWORD_CHANGED = "password_changed", "Password changed"
    DEVICE_REVOKED = "device_revoked", "Device revoked"


class SecurityEvent(UUIDPrimaryKeyModel, TimeStampedModel):
    """Append-only security audit log (no soft-delete; never mutated)."""

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="security_events",
    )
    event_type = models.CharField(
        max_length=32,
        choices=SecurityEventType.choices,
        db_index=True,
    )
    # Captured even when no user matches (e.g. failed login for unknown email).
    email = models.EmailField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Security event"
        verbose_name_plural = "Security events"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["user", "event_type"]),
            models.Index(fields=["event_type", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} @ {self.created_at:%Y-%m-%d %H:%M:%S}"
