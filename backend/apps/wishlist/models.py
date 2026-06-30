"""Wishlist model (store-scoped via ``TenantOwnedModel``).

A flat per-buyer list of saved product variants within a store. One row per
(store, user, variant); items can be moved into the cart.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.models import TenantOwnedModel


class WishlistItem(TenantOwnedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist_items"
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant", on_delete=models.CASCADE, related_name="+"
    )

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Wishlist item"
        verbose_name_plural = "Wishlist items"
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["store", "user", "variant"],
                condition=Q(is_deleted=False),
                name="uniq_wishlist_store_user_variant",
            )
        ]
        indexes = [models.Index(fields=["store", "user"])]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.variant_id}"
