"""Store access control helpers (RBAC over StoreMembership)."""

from __future__ import annotations

from apps.core.exceptions import NotFoundError, PermissionDeniedError
from apps.stores.models import Store, StoreRole
from apps.stores.repositories import StoreMembershipRepository, StoreRepository

# Role groupings used by views.
MANAGER_OR_OWNER = {StoreRole.OWNER, StoreRole.MANAGER}
OWNER_ONLY = {StoreRole.OWNER}


class StoreAccessMixin:
    """Loads the store from the URL and enforces the caller's membership role.

    On success, sets ``self.membership`` and returns the ``Store``. Raises
    ``NotFoundError`` (unknown store) or ``PermissionDeniedError`` (not a member /
    insufficient role).
    """

    def load_store(self, store_id, *, roles: set | None = None) -> Store:
        store = StoreRepository().get_or_none(id=store_id)
        if store is None:
            raise NotFoundError("Store not found.")
        membership = StoreMembershipRepository().active_membership(
            store=store, user=self.request.user
        )
        if membership is None:
            raise PermissionDeniedError("You are not a member of this store.")
        if roles is not None and membership.role not in roles:
            raise PermissionDeniedError("You do not have the required store role for this action.")
        self.membership = membership
        return store
