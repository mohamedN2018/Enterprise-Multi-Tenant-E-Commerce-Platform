"""Reusable base permissions.

Generic, composable building blocks. Store/role-scoped and object-level
permissions for tenant membership are layered on top of these in later features.
"""

from __future__ import annotations

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthenticatedAndActive(BasePermission):
    message = "Authentication credentials were not provided or the account is inactive."

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and user.is_active)


class IsSuperAdmin(BasePermission):
    message = "Super-administrator privileges are required."

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and user.is_superuser)


class IsStaff(BasePermission):
    message = "Staff privileges are required."

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and user.is_staff)


class ReadOnly(BasePermission):
    """Allow only safe (GET/HEAD/OPTIONS) methods."""

    def has_permission(self, request, view) -> bool:
        return request.method in SAFE_METHODS


class IsObjectOwnerOrReadOnly(BasePermission):
    """Object-level: writes require ownership; reads are open.

    Ownership is inferred from a common attribute on the object
    (``created_by``, ``owner`` or ``user``).
    """

    owner_fields = ("created_by", "owner", "user")

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if not (user and user.is_authenticated):
            return False
        for field in self.owner_fields:
            if hasattr(obj, field):
                return getattr(obj, field) == user
        return False
