"""Store access control helpers (RBAC over StoreMembership)."""

from __future__ import annotations

from apps.core.exceptions import NotFoundError, PermissionDeniedError
from apps.stores.models import Store, StoreMembership, StoreRole
from apps.stores.repositories import StoreMembershipRepository, StoreRepository

# Role groupings used by views.
MANAGER_OR_OWNER = {StoreRole.OWNER, StoreRole.MANAGER}
OWNER_ONLY = {StoreRole.OWNER}


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
