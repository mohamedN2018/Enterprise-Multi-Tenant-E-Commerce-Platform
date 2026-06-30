"""Admin registration for wishlist."""

from __future__ import annotations

from django.contrib import admin

from apps.wishlist.models import WishlistItem


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ("user", "variant", "store", "created_at")
    search_fields = ("user__email", "variant__sku", "store__name")
