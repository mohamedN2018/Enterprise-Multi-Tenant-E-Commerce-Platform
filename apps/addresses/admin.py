"""Admin registration for addresses."""

from __future__ import annotations

from django.contrib import admin

from apps.addresses.models import Address


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "store", "city", "country", "is_default")
    list_filter = ("country", "is_default")
    search_fields = ("full_name", "city", "user__email", "store__name")
