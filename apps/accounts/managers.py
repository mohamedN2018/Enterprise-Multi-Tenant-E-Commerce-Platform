"""Managers for the accounts app."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib.auth.models import BaseUserManager
from django.db import models
from django.utils import timezone

from apps.core.managers import SoftDeleteQuerySet

if TYPE_CHECKING:  # pragma: no cover
    from apps.accounts.models import User


class UserQuerySet(SoftDeleteQuerySet):
    pass


class UserManager(BaseUserManager.from_queryset(UserQuerySet)):
    """Default manager: excludes soft-deleted users and centralises creation."""

    use_in_migrations = True

    def get_queryset(self) -> UserQuerySet:
        return super().get_queryset().filter(is_deleted=False)

    def _create_user(self, email: str, password: str | None, **extra_fields: Any) -> User:
        if not email:
            raise ValueError("Users must have an email address.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields: Any) -> User:
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(
        self, email: str, password: str | None = None, **extra_fields: Any
    ) -> User:
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        # Superusers are created out-of-band and are implicitly trusted.
        extra_fields.setdefault("is_verified", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class OneTimeTokenQuerySet(SoftDeleteQuerySet):
    def valid(self) -> OneTimeTokenQuerySet:
        return self.filter(
            is_deleted=False,
            used_at__isnull=True,
            expires_at__gt=timezone.now(),
        )


class OneTimeTokenManager(models.Manager.from_queryset(OneTimeTokenQuerySet)):
    def get_queryset(self) -> OneTimeTokenQuerySet:
        return super().get_queryset().filter(is_deleted=False)
