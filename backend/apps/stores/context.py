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
from apps.stores.access import APP_PERMISSION_AREA, MANAGER_OR_OWNER, _superuser_membership
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
        user = request.user
        if getattr(user, "is_superuser", False):
            # Platform admins act as owner of every store.
            self.membership = _superuser_membership(self.store, user)
            return
        membership = StoreMembershipRepository().active_membership(
            store=self.store, user=user
        )
        if membership is None:
            raise PermissionDeniedError("You are not a member of this store.")
        self.membership = membership

    def require_write(self, area: str | None = None) -> None:
        """Gate a mutation. Owners/managers (and platform admins via god-mode)
        may write anything; an EMPLOYEE may write only the areas the owner
        granted them. The area is derived from the view's app unless passed."""
        membership = self.membership
        if membership.role in self.write_roles:
            return
        if area is None:
            area = self._write_area()
        granted = getattr(membership, "permissions", None) or []
        if area and area in granted:
            return
        raise PermissionDeniedError("You do not have permission to modify this store's data.")

    def _write_area(self) -> str | None:
        # View module is 'apps.<app>.<something>' → map the app to its area.
        parts = type(self).__module__.split(".")
        app = parts[1] if len(parts) > 2 and parts[0] == "apps" else ""
        return APP_PERMISSION_AREA.get(app)
