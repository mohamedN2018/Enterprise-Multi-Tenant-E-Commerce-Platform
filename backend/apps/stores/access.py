"""Store access control helpers (RBAC over StoreMembership)."""

from __future__ import annotations

from apps.core.exceptions import NotFoundError, PermissionDeniedError
from apps.stores.models import Store, StoreMembership, StoreRole
from apps.stores.repositories import StoreMembershipRepository, StoreRepository

# Role groupings used by views.
MANAGER_OR_OWNER = {StoreRole.OWNER, StoreRole.MANAGER}
OWNER_ONLY = {StoreRole.OWNER}

# --- Granular employee permissions -----------------------------------------
# Owners/managers can write everything. An EMPLOYEE writes only the "areas" the
# owner granted them (stored on StoreMembership.permissions). Areas are coarse,
# business-facing sections — not one per endpoint.
PERMISSION_AREAS = (
    "catalog",    # products, categories, brands, attributes
    "inventory",  # stock
    "sales",      # orders, returns, payments, reviews
    "marketing",  # promotions, campaigns, gift cards, pricing
    "shipping",   # shipping, procurement
    "finance",    # payouts, finance, fraud
    "settings",   # store settings, notifications
)

# Map each Django app to the permission area it belongs to. The write-check
# derives the area from the view's module, so no per-view tagging is needed.
APP_PERMISSION_AREA = {
    "catalog": "catalog",
    "inventory": "inventory",
    "orders": "sales",
    "returns": "sales",
    "payments": "sales",
    "reviews": "sales",
    "promotions": "marketing",
    "pricing": "marketing",
    "shipping": "shipping",
    "procurement": "shipping",
    "payouts": "finance",
    "finance": "finance",
    "fraud": "finance",
    "notifications": "settings",
    "stores": "settings",
}


def _superuser_membership(store, user) -> StoreMembership:
    """Synthetic (unsaved) owner membership so platform admins act as the owner
    of any store, while downstream ``self.membership.role`` checks keep working."""
    return StoreMembership(store=store, user=user, role=StoreRole.OWNER, is_active=True)


class StoreAccessMixin:
    """Loads the store from the URL and enforces the caller's membership role.

    On success, sets ``self.membership`` and returns the ``Store``. Raises
    ``NotFoundError`` (unknown store) or ``PermissionDeniedError`` (not a member /
    insufficient role). Superusers (platform admins) bypass membership entirely.
    """

    def load_store(self, store_id, *, roles: set | None = None) -> Store:
        store = StoreRepository().get_or_none(id=store_id)
        if store is None:
            raise NotFoundError("Store not found.")
        user = self.request.user
        if getattr(user, "is_superuser", False):
            self.membership = _superuser_membership(store, user)
            return store
        membership = StoreMembershipRepository().active_membership(store=store, user=user)
        if membership is None:
            raise PermissionDeniedError("You are not a member of this store.")
        if roles is not None and membership.role not in roles:
            raise PermissionDeniedError("You do not have the required store role for this action.")
        self.membership = membership
        return store
