"""Admin registration for the custom user model."""
from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.forms import UserCreationForm, UserChangeForm
from apps.accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    model = User

    ordering = ("-created_at",)
    list_display = (
        "email",
        "is_active",
        "is_staff",
        "is_superuser",
        "is_deleted",
        "created_at",
    )
    list_filter = ("is_active", "is_staff", "is_superuser", "is_deleted")
    search_fields = ("email",)
    readonly_fields = ("id", "last_login", "created_at", "updated_at")
    filter_horizontal = ("groups", "user_permissions")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        ("Soft delete", {"fields": ("is_deleted", "deleted_at")}),
        ("Audit", {"fields": ("id", "last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2"),
        }),
    )
