"""Catalog store-context access control.

Re-exports the shared :class:`apps.stores.context.StoreContextMixin` so existing
imports (``apps.catalog.access.StoreContextMixin``) keep working.
"""

from __future__ import annotations

from apps.stores.context import StoreContextMixin

__all__ = ["StoreContextMixin"]
