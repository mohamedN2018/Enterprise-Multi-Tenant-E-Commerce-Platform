"""Abstract base models — the building blocks every domain model composes.

Mix-ins (single responsibility each):
    * UUIDPrimaryKeyModel  — non-sequential UUIDv4 primary key (no enumeration).
    * TimeStampedModel      — created_at / updated_at.
    * SoftDeleteModel       — is_deleted / deleted_at / deleted_by + soft delete.
    * AuditModel            — created_by / updated_by.

``BaseModel`` composes all four and auto-stamps the audit fields from the
request actor (see :mod:`apps.core.tenancy`). Domain models should subclass
``BaseModel`` unless they need a narrower contract.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core import tenancy
from apps.core.managers import AllObjectsManager, SoftDeleteManager


class UUIDPrimaryKeyModel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True
        get_latest_by = "created_at"


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False, db_index=True, editable=False)
    deleted_at = models.DateTimeField(null=True, blank=True, editable=False)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        editable=False,
    )

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True
        # Keep cascades / related lookups correct: the *base* manager must not
        # filter soft-deleted rows.
        base_manager_name = "all_objects"

    def delete(self, using=None, keep_parents=False, *, hard=False):
        """Soft-delete by default; pass ``hard=True`` to remove permanently."""
        if hard:
            return super().delete(using=using, keep_parents=keep_parents)
        self.is_deleted = True
        self.deleted_at = timezone.now()
        actor = tenancy.get_current_user()
        if actor is not None and getattr(actor, "is_authenticated", False):
            self.deleted_by = actor
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])
        return 1, {self._meta.label: 1}

    def restore(self) -> None:
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])


class AuditModel(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        editable=False,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        editable=False,
    )

    class Meta:
        abstract = True


class BaseModel(UUIDPrimaryKeyModel, TimeStampedModel, AuditModel, SoftDeleteModel):
    """Standard base for domain models: UUID PK + timestamps + audit + soft-delete."""

    class Meta(SoftDeleteModel.Meta):
        abstract = True

    def save(self, *args, **kwargs):
        actor = tenancy.get_current_user()
        if actor is not None and getattr(actor, "is_authenticated", False):
            if self._state.adding and self.created_by_id is None:
                self.created_by = actor
            self.updated_by = actor
        super().save(*args, **kwargs)
