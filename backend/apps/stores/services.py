"""Application services for the stores app."""

from __future__ import annotations

from django.utils.text import slugify

from apps.accounts.repositories import UserRepository
from apps.core.exceptions import ConflictError, NotFoundError, ValidationError
from apps.core.services import BaseService, atomic
from apps.stores.models import (
    Store,
    StoreMembership,
    StoreRole,
    StoreSettings,
    StoreStatus,
)
from apps.stores.repositories import StoreMembershipRepository, StoreRepository

_UPDATABLE_STORE_FIELDS = (
    "name",
    "description",
    "email",
    "phone",
    "status",
    "currency",
    "language",
    "timezone",
    "country",
    "logo",
    "banner",
)
_MANAGEABLE_ROLES = {StoreRole.MANAGER, StoreRole.EMPLOYEE}


class StoreService(BaseService):
    def __init__(
        self,
        *,
        store_repo: StoreRepository | None = None,
        membership_repo: StoreMembershipRepository | None = None,
    ) -> None:
        self.store_repo = store_repo or StoreRepository()
        self.membership_repo = membership_repo or StoreMembershipRepository()

    @atomic
    def create_store(self, *, owner, data: dict) -> Store:
        slug = data.get("slug") or self._unique_slug(data["name"])
        store = self.store_repo.create(
            name=data["name"],
            slug=slug,
            owner=owner,
            description=data.get("description", ""),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            currency=data.get("currency", "USD"),
            language=data.get("language", "en"),
            timezone=data.get("timezone", "UTC"),
            country=data.get("country", ""),
            status=StoreStatus.DRAFT,
        )
        StoreSettings.objects.create(store=store)
        self.membership_repo.create(store=store, user=owner, role=StoreRole.OWNER, is_active=True)
        return store

    @atomic
    def update_store(self, *, store: Store, data: dict) -> Store:
        for field in _UPDATABLE_STORE_FIELDS:
            if field in data:
                setattr(store, field, data[field])
        store.save()
        return store

    def delete_store(self, *, store: Store) -> None:
        store.delete()  # soft delete

    @atomic
    def update_settings(self, *, store: Store, data: dict) -> StoreSettings:
        settings_obj = store.settings
        for field, value in data.items():
            setattr(settings_obj, field, value)
        settings_obj.save()
        return settings_obj

    def _unique_slug(self, name: str) -> str:
        base = slugify(name)[:240] or "store"
        slug = base
        suffix = 1
        while self.store_repo.slug_exists(slug):
            suffix += 1
            slug = f"{base}-{suffix}"
        return slug


class MembershipService(BaseService):
    def __init__(
        self,
        *,
        membership_repo: StoreMembershipRepository | None = None,
        user_repo: UserRepository | None = None,
    ) -> None:
        self.repo = membership_repo or StoreMembershipRepository()
        self.user_repo = user_repo or UserRepository()

    def list_members(self, store: Store):
        return self.repo.members(store)

    def get_member(self, *, store: Store, member_id) -> StoreMembership:
        membership = self.repo.get_or_none(id=member_id, store=store)
        if membership is None:
            raise NotFoundError("Membership not found.")
        return membership

    @atomic
    def add_member(self, *, store: Store, email: str, role: str, invited_by) -> StoreMembership:
        self._assert_manageable_role(role)
        user = self.user_repo.get_by_email(email)
        if user is None:
            raise ValidationError(
                "No user found with this email address.",
                code="user_not_found",
                errors={"email": ["No user found with this email address."]},
            )
        existing = self.repo.get_membership(store=store, user=user)
        if existing is not None:
            if existing.is_deleted:
                existing.restore()
                existing.role = role
                existing.is_active = True
                existing.invited_by = invited_by
                existing.save(update_fields=["role", "is_active", "invited_by", "updated_at"])
                return existing
            raise ConflictError(
                "This user is already a member of the store.", code="already_member"
            )
        return self.repo.create(
            store=store, user=user, role=role, is_active=True, invited_by=invited_by
        )

    @atomic
    def change_role(
        self, *, store: Store, membership: StoreMembership, role: str
    ) -> StoreMembership:
        if membership.user_id == store.owner_id:
            raise ValidationError(
                "The store owner's role cannot be changed.", code="owner_immutable"
            )
        self._assert_manageable_role(role)
        membership.role = role
        membership.save(update_fields=["role", "updated_at"])
        return membership

    @atomic
    def remove_member(self, *, store: Store, membership: StoreMembership) -> None:
        if membership.user_id == store.owner_id:
            raise ValidationError("The store owner cannot be removed.", code="owner_immutable")
        membership.delete()  # soft delete

    @staticmethod
    def _assert_manageable_role(role: str) -> None:
        if role not in _MANAGEABLE_ROLES:
            raise ValidationError(
                "Role must be 'manager' or 'employee'.",
                code="invalid_role",
                errors={"role": ["Role must be 'manager' or 'employee'."]},
            )
