"""Application services for the stores app."""

from __future__ import annotations

from django.utils import timezone
from django.utils.text import slugify

from apps.accounts.repositories import UserRepository
from apps.core.exceptions import ConflictError, NotFoundError, ValidationError
from apps.core.services import BaseService, atomic
from apps.stores.models import (
    LimitRequest,
    LimitRequestKind,
    LimitRequestStatus,
    Store,
    StoreMembership,
    StoreRole,
    StoreSettings,
    StoreStatus,
)
from apps.stores.repositories import StoreMembershipRepository, StoreRepository

_UPDATABLE_STORE_FIELDS = (
    "name",
    "name_en",
    "description",
    "description_en",
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
    def create_store(self, *, owner, data: dict, enforce_limit: bool = True) -> Store:
        if enforce_limit and self.store_repo.owned_count(owner) >= owner.max_stores:
            raise ValidationError(
                f"Store limit reached ({owner.max_stores}). "
                "Contact the platform admin to raise it.",
                code="store_limit_reached",
            )
        slug = data.get("slug") or self._unique_slug(data["name"])
        store = self.store_repo.create(
            name=data["name"],
            name_en=data.get("name_en", ""),
            slug=slug,
            owner=owner,
            description=data.get("description", ""),
            description_en=data.get("description_en", ""),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            currency=data.get("currency", "EGP"),
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
    def add_member(
        self, *, store: Store, email: str, role: str, invited_by, permissions=None
    ) -> StoreMembership:
        self._assert_manageable_role(role)
        perms = self._perms_for(role, permissions)
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
                # Re-activating a former member counts as adding an employee again.
                if role == StoreRole.EMPLOYEE:
                    self._assert_employee_capacity(store)
                existing.restore()
                existing.role = role
                existing.permissions = perms
                existing.is_active = True
                existing.invited_by = invited_by
                existing.save(
                    update_fields=["role", "permissions", "is_active", "invited_by", "updated_at"]
                )
                return existing
            raise ConflictError(
                "This user is already a member of the store.", code="already_member"
            )
        if role == StoreRole.EMPLOYEE:
            self._assert_employee_capacity(store)
        return self.repo.create(
            store=store, user=user, role=role, permissions=perms, is_active=True, invited_by=invited_by
        )

    @staticmethod
    def _perms_for(role: str, permissions) -> list:
        # Only employees carry a permission set; managers/owners write everything.
        return list(permissions or []) if role == StoreRole.EMPLOYEE else []

    def _assert_employee_capacity(self, store: Store) -> None:
        cap = store.settings.max_employees
        if self.repo.employee_count(store) >= cap:
            raise ValidationError(
                f"Employee limit reached ({cap}). Ask the platform admin to raise it.",
                code="employee_limit_reached",
                errors={"role": [f"Employee limit reached ({cap})."]},
            )

    @atomic
    def change_role(
        self, *, store: Store, membership: StoreMembership, role: str, permissions=None
    ) -> StoreMembership:
        if membership.user_id == store.owner_id:
            raise ValidationError(
                "The store owner's role cannot be changed.", code="owner_immutable"
            )
        self._assert_manageable_role(role)
        membership.role = role
        membership.permissions = self._perms_for(role, permissions)
        membership.save(update_fields=["role", "permissions", "updated_at"])
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


class LimitRequestService(BaseService):
    """Seller-raised requests to lift a cap; a platform admin approves/rejects."""

    @atomic
    def create(self, *, requested_by, store, kind, requested_limit, note=""):
        if kind == LimitRequestKind.EMPLOYEES:
            current = store.settings.max_employees
            pending_qs = LimitRequest.objects.filter(
                store=store, kind=kind, status=LimitRequestStatus.PENDING
            )
        else:
            current = requested_by.max_stores
            pending_qs = LimitRequest.objects.filter(
                requested_by=requested_by, kind=kind, status=LimitRequestStatus.PENDING
            )
        if requested_limit <= current:
            raise ValidationError(
                "The requested limit must be higher than the current one.",
                code="invalid_limit",
                errors={"requested_limit": ["Must be higher than the current limit."]},
            )
        if pending_qs.exists():
            raise ConflictError("A pending request already exists.", code="request_pending")
        return LimitRequest.objects.create(
            requested_by=requested_by,
            store=store,
            kind=kind,
            current_limit=current,
            requested_limit=requested_limit,
            note=note,
        )

    @atomic
    def approve(self, *, request_obj, resolver):
        self._assert_pending(request_obj)
        if request_obj.kind == LimitRequestKind.EMPLOYEES:
            settings_obj = request_obj.store.settings
            settings_obj.max_employees = request_obj.requested_limit
            settings_obj.save(update_fields=["max_employees", "updated_at"])
        else:
            owner = request_obj.requested_by
            owner.max_stores = request_obj.requested_limit
            owner.save(update_fields=["max_stores", "updated_at"])
        return self._resolve(request_obj, LimitRequestStatus.APPROVED, resolver)

    @atomic
    def reject(self, *, request_obj, resolver):
        self._assert_pending(request_obj)
        return self._resolve(request_obj, LimitRequestStatus.REJECTED, resolver)

    @staticmethod
    def _assert_pending(request_obj) -> None:
        if request_obj.status != LimitRequestStatus.PENDING:
            raise ValidationError(
                "This request has already been resolved.", code="already_resolved"
            )

    @staticmethod
    def _resolve(request_obj, status, resolver):
        request_obj.status = status
        request_obj.resolved_by = resolver
        request_obj.resolved_at = timezone.now()
        request_obj.save(update_fields=["status", "resolved_by", "resolved_at", "updated_at"])
        return request_obj
