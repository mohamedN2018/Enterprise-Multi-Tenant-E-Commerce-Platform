"""Reusable managers & querysets: soft-delete and tenant scoping.

Design notes
------------
* ``objects`` (default manager) hides soft-deleted rows. ``all_objects`` sees
  everything and is registered as ``Meta.base_manager_name`` so that related
  lookups and cascade collection are NOT silently filtered (a documented Django
  pitfall when the default manager filters rows).
* QuerySet-level ``delete()`` performs a *bulk* soft-delete. Note this does not
  cascade soft-deletion to related objects — that is intentionally explicit and
  handled in service layers where the business rules live.
"""
from __future__ import annotations

from django.db import models
from django.utils import timezone

from apps.core import tenancy


class SoftDeleteQuerySet(models.QuerySet):
    def alive(self) -> "SoftDeleteQuerySet":
        return self.filter(is_deleted=False)

    def dead(self) -> "SoftDeleteQuerySet":
        return self.filter(is_deleted=True)

    def delete(self):  # type: ignore[override]
        """Bulk soft-delete: mark rows deleted instead of removing them."""
        return self.update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        """Permanently remove rows (bypasses soft-delete)."""
        return super().delete()

    def restore(self):
        return self.update(is_deleted=False, deleted_at=None, deleted_by=None)


class SoftDeleteManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    """Default manager — excludes soft-deleted rows."""

    def get_queryset(self) -> SoftDeleteQuerySet:
        return super().get_queryset().filter(is_deleted=False)


class AllObjectsManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    """Escape hatch / base manager — includes soft-deleted rows."""


class TenantQuerySet(SoftDeleteQuerySet):
    def for_store(self, store) -> "TenantQuerySet":
        return self.filter(store=store)


class TenantManager(models.Manager.from_queryset(TenantQuerySet)):
    """Default manager for tenant-owned models.

    Automatically scopes queries to the current store (resolved from the
    request/task context) and hides soft-deleted rows. When no store is bound
    (e.g. platform-admin / cross-tenant jobs) it falls back to all stores, so
    privileged code paths must scope explicitly.
    """

    def get_queryset(self) -> TenantQuerySet:
        qs = super().get_queryset().filter(is_deleted=False)
        store = tenancy.get_current_store()
        if store is not None:
            qs = qs.filter(store=store)
        return qs


class TenantAllObjectsManager(models.Manager.from_queryset(TenantQuerySet)):
    """Unscoped manager for tenant-owned models (no store/soft-delete filter)."""
