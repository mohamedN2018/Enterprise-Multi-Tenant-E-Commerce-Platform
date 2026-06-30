"""Admin registration for stores."""

from __future__ import annotations

from django.contrib import admin

from apps.stores.models import Store, StoreMembership, StoreSettings


class StoreSettingsInline(admin.StackedInline):
    model = StoreSettings
    extra = 0
    can_delete = False


class StoreMembershipInline(admin.TabularInline):
    model = StoreMembership
    extra = 0
    fields = ("user", "role", "is_active", "invited_by")
    autocomplete_fields = ("user", "invited_by")


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "owner", "status", "is_verified", "created_at")
    list_filter = ("status", "is_verified", "currency")
    search_fields = ("name", "slug", "owner__email")
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("owner",)
    inlines = (StoreSettingsInline, StoreMembershipInline)


@admin.register(StoreMembership)
class StoreMembershipAdmin(admin.ModelAdmin):
    list_display = ("store", "user", "role", "is_active", "created_at")
    list_filter = ("role", "is_active")
    search_fields = ("store__name", "user__email")
    autocomplete_fields = ("store", "user", "invited_by")
