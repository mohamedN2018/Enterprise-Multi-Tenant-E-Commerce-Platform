"""Shared store-context access mixins for tenant-scoped API views.

* ``RequireStoreMixin``   — requires a resolved store (from the X-Store-Id /
  X-Store-Slug header). Used by buyer-facing endpoints (cart/orders); any
  authenticated user may act within a store.
* ``StoreContextMixin``   — additionally requires the caller to be an active
  member; ``require_write`` gates mutations to manager/owner. Used by staff
  endpoints (catalog/inventory).
"""

from __future__ import annotations

from apps.core import tenancy
from apps.core.exceptions import PermissionDeniedError, ValidationError
from apps.stores.access import MANAGER_OR_OWNER
from apps.stores.repositories import StoreMembershipRepository


class RequireStoreMixin:
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)  # auth + actor binding
        store = tenancy.get_current_store()
        if store is None:
            raise ValidationError(
                "Store context is required. Provide an X-Store-Id or X-Store-Slug header.",
                code="store_context_required",
            )
        self.store = store


class StoreContextMixin(RequireStoreMixin):
    write_roles = MANAGER_OR_OWNER

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)  # sets self.store
        membership = StoreMembershipRepository().active_membership(
            store=self.store, user=request.user
        )
        if membership is None:
            raise PermissionDeniedError("You are not a member of this store.")
        self.membership = membership

    def require_write(self) -> None:
        if self.membership.role not in self.write_roles:
            raise PermissionDeniedError("You do not have permission to modify this store's data.")
