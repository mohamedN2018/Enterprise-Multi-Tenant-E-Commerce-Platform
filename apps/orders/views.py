"""Cart & order API views (buyer-facing).

Require a store context (X-Store-Id / X-Store-Slug header) + authentication, but
NOT store membership — buyers are not staff. The acting buyer is ``request.user``.
"""

from __future__ import annotations

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.exceptions import NotFoundError
from apps.core.mixins import BaseAPIView, BaseGenericAPIView
from apps.core.responses import APIResponse
from apps.orders.models import CartItem, CartStatus, Order
from apps.orders.serializers import (
    AddCartItemSerializer,
    CartItemSerializer,
    CartSerializer,
    OrderSerializer,
    UpdateCartItemSerializer,
)
from apps.orders.services import CartService, CheckoutService
from apps.stores.context import RequireStoreMixin


class CartView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        cart = CartService().get_active_cart(store=self.store, user=request.user)
        return APIResponse.success(CartSerializer(cart).data)

    def delete(self, request: Request) -> Response:
        cart = CartService().get_active_cart(store=self.store, user=request.user)
        CartService().clear(cart=cart)
        return APIResponse.success(message="Cart cleared.")


class CartItemCreateView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = AddCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = CartService().add_item(
            store=self.store,
            user=request.user,
            variant_id=serializer.validated_data["variant_id"],
            quantity=serializer.validated_data["quantity"],
        )
        return APIResponse.success(
            CartItemSerializer(item).data, message="Item added to cart.", status_code=201
        )


class CartItemDetailView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def _get_item(self, request, item_id) -> CartItem:
        item = (
            CartItem.objects.filter(
                id=item_id, cart__user=request.user, cart__status=CartStatus.ACTIVE
            )
            .select_related("variant__product")
            .first()
        )
        if item is None:
            raise NotFoundError("Cart item not found.")
        return item

    def patch(self, request: Request, item_id) -> Response:
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = self._get_item(request, item_id)
        updated = CartService().update_item(
            item=item, quantity=serializer.validated_data["quantity"]
        )
        if updated is None:
            return APIResponse.success(message="Item removed from cart.")
        return APIResponse.success(CartItemSerializer(updated).data, message="Cart updated.")

    def delete(self, request: Request, item_id) -> Response:
        item = self._get_item(request, item_id)
        CartService().remove_item(item=item)
        return APIResponse.success(message="Item removed from cart.")


class CheckoutView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        order = CheckoutService().checkout(store=self.store, user=request.user)
        return APIResponse.success(
            OrderSerializer(order).data, message="Order placed.", status_code=201
        )


class OrderListView(RequireStoreMixin, BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    filterset_fields = ("status",)

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related("items")


class OrderDetailView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def _get_order(self, request, order_id) -> Order:
        order = (
            Order.objects.filter(id=order_id, user=request.user).prefetch_related("items").first()
        )
        if order is None:
            raise NotFoundError("Order not found.")
        return order

    def get(self, request: Request, order_id) -> Response:
        order = self._get_order(request, order_id)
        return APIResponse.success(OrderSerializer(order).data)


class OrderConfirmView(OrderDetailView):
    def post(self, request: Request, order_id) -> Response:
        order = self._get_order(request, order_id)
        order = CheckoutService().confirm_order(order=order)
        return APIResponse.success(OrderSerializer(order).data, message="Order confirmed.")


class OrderCancelView(OrderDetailView):
    def post(self, request: Request, order_id) -> Response:
        order = self._get_order(request, order_id)
        order = CheckoutService().cancel_order(order=order)
        return APIResponse.success(OrderSerializer(order).data, message="Order cancelled.")
