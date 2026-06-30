"""Wishlist application service: add/remove items and move them into the cart."""

from __future__ import annotations

from apps.core.exceptions import NotFoundError
from apps.core.services import BaseService, atomic
from apps.wishlist.models import WishlistItem


class WishlistService(BaseService):
    @atomic
    def add(self, *, store, user, variant) -> WishlistItem:
        item, _ = WishlistItem.objects.get_or_create(store=store, user=user, variant=variant)
        return item

    def list_items(self, *, store, user):
        return WishlistItem.objects.filter(store=store, user=user).select_related(
            "variant__product"
        )

    def get_item(self, *, store, user, item_id) -> WishlistItem:
        item = WishlistItem.objects.filter(store=store, user=user, id=item_id).first()
        if item is None:
            raise NotFoundError("Wishlist item not found.")
        return item

    def remove(self, *, item: WishlistItem) -> None:
        item.delete()

    @atomic
    def move_to_cart(self, *, store, user, item: WishlistItem, quantity: int = 1):
        from apps.orders.services import CartService

        cart_item = CartService().add_item(
            store=store, user=user, variant_id=item.variant_id, quantity=quantity
        )
        item.delete()
        return cart_item
