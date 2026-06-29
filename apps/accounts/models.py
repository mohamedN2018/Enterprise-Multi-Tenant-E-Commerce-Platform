"""Authentication identity.

``User`` is the platform-wide authentication account (store owners, managers,
employees, platform staff, super-admins). It uses email as the login identifier
and a UUID primary key.

Per the chosen topology (isolated, Shopify-style stores), *customer* identity is
store-scoped and modelled separately in a later feature — it does not change
``AUTH_USER_MODEL``. Rich profile data (name, avatar, phones, addresses) is added
incrementally in the user-management feature; this model stays auth-focused.
"""
from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from apps.accounts.managers import UserManager
from apps.core.managers import AllObjectsManager
from apps.core.models import BaseModel


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
