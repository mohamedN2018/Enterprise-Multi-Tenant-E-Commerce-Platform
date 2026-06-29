"""Shared store-context access mixin for tenant-scoped API views.

Requires an active store (resolved from the X-Store-Id / X-Store-Slug header by
the tenancy middleware) and an active membership for the caller. Reads are open
to any member; writes require manager/owner (call ``require_write``).
"""

from __future__ import annotations

from apps.core import tenancy
from apps.core.exceptions import PermissionDeniedError, ValidationError
from apps.stores.access import MANAGER_OR_OWNER
from apps.stores.repositories import StoreMembershipRepository


class StoreContextMixin:
    write_roles = MANAGER_OR_OWNER

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)  # auth + actor binding
        store = tenancy.get_current_store()
        if store is None:
            raise ValidationError(
                "Store context is required. Provide an X-Store-Id or X-Store-Slug header.",
                code="store_context_required",
            )
        membership = StoreMembershipRepository().active_membership(store=store, user=request.user)
        if membership is None:
            raise PermissionDeniedError("You are not a member of this store.")
        self.store = store
        self.membership = membership

    def require_write(self) -> None:
        if self.membership.role not in self.write_roles:
            raise PermissionDeniedError("You do not have permission to modify this store's data.")
