"""Wishlist API (buyer-facing): save variants and move them into the cart."""

from __future__ import annotations

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.catalog.models import ProductVariant
from apps.core.exceptions import ValidationError
from apps.core.mixins import BaseAPIView, BaseGenericAPIView
from apps.core.responses import APIResponse
from apps.orders.serializers import CartItemSerializer
from apps.stores.context import RequireStoreMixin
from apps.wishlist.serializers import (
    AddWishlistItemSerializer,
    MoveToCartSerializer,
    WishlistItemSerializer,
)
from apps.wishlist.services import WishlistService


class WishlistListCreateView(RequireStoreMixin, BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WishlistItemSerializer

    def get_queryset(self):
        return WishlistService().list_items(store=self.store, user=self.request.user)

    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = AddWishlistItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        variant = ProductVariant.objects.filter(
            id=serializer.validated_data["variant_id"], is_active=True
        ).first()
        if variant is None:
            raise ValidationError(
                "Variant not found in this store.",
                code="variant_unavailable",
                errors={"variant_id": ["Not available in this store."]},
            )
        item = WishlistService().add(store=self.store, user=request.user, variant=variant)
        return APIResponse.success(
            WishlistItemSerializer(item).data, message="Added to wishlist.", status_code=201
        )


class WishlistItemDetailView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request: Request, item_id) -> Response:
        service = WishlistService()
        service.remove(item=service.get_item(store=self.store, user=request.user, item_id=item_id))
        return APIResponse.success(message="Removed from wishlist.")


class WishlistMoveToCartView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, item_id) -> Response:
        serializer = MoveToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = WishlistService()
        cart_item = service.move_to_cart(
            store=self.store,
            user=request.user,
            item=service.get_item(store=self.store, user=request.user, item_id=item_id),
            quantity=serializer.validated_data["quantity"],
        )
        return APIResponse.success(
            CartItemSerializer(cart_item).data, message="Moved to cart.", status_code=201
        )
