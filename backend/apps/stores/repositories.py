"""Data-access repositories for the stores app."""

from __future__ import annotations

from django.db.models import QuerySet

from apps.accounts.models import User
from apps.core.repositories import BaseRepository
from apps.stores.models import Store, StoreMembership


class StoreRepository(BaseRepository[Store]):
    model = Store

    def get_by_slug(self, slug: str) -> Store | None:
        return self.get_or_none(slug=slug)

    def slug_exists(self, slug: str) -> bool:
        return Store.all_objects.filter(slug=slug).exists()

    def for_member(self, user: User) -> QuerySet[Store]:
        """Stores the user is an active member of."""
        return Store.objects.filter(memberships__user=user, memberships__is_active=True).distinct()


class StoreMembershipRepository(BaseRepository[StoreMembership]):
    model = StoreMembership

    def get_membership(self, *, store: Store, user) -> StoreMembership | None:
        return self.get_or_none(store=store, user=user)

    def active_membership(self, *, store: Store, user) -> StoreMembership | None:
        return self.get_or_none(store=store, user=user, is_active=True)

    def members(self, store: Store) -> QuerySet[StoreMembership]:
        return (
            StoreMembership.objects.filter(store=store)
            .select_related("user", "invited_by")
            .order_by("role", "created_at")
        )
