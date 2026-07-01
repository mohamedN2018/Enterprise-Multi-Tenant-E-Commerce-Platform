"""Cart & order API views (buyer-facing).

Require a store context (X-Store-Id / X-Store-Slug header) + authentication, but
NOT store membership — buyers are not staff. The acting buyer is ``request.user``.
"""

from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
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
    CheckoutSerializer,
    OrderSerializer,
    UpdateCartItemSerializer,
)
from apps.orders.services import CartService, CheckoutService
from apps.promotions.serializers import ApplyCouponSerializer
from apps.stores.context import RequireStoreMixin, StoreContextMixin


@extend_schema(tags=["Cart"])
class CartView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=CartSerializer)
    def get(self, request: Request) -> Response:
        cart = CartService().read_cart(store=self.store, user=request.user)
        return APIResponse.success(CartSerializer(cart).data)

    @extend_schema(responses=OpenApiResponse(description="Cart cleared."))
    def delete(self, request: Request) -> Response:
        cart = CartService().get_active_cart(store=self.store, user=request.user)
        CartService().clear(cart=cart)
        return APIResponse.success(message="Cart cleared.")


@extend_schema(tags=["Cart"])
class CartItemCreateView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=AddCartItemSerializer, responses=CartItemSerializer)
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


@extend_schema(tags=["Cart"])
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

    @extend_schema(request=UpdateCartItemSerializer, responses=CartItemSerializer)
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

    @extend_schema(responses=OpenApiResponse(description="Item removed from cart."))
    def delete(self, request: Request, item_id) -> Response:
        item = self._get_item(request, item_id)
        CartService().remove_item(item=item)
        return APIResponse.success(message="Item removed from cart.")


@extend_schema(tags=["Cart"])
class CartCouponView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=ApplyCouponSerializer, responses=CartSerializer)
    def post(self, request: Request) -> Response:
        serializer = ApplyCouponSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = CartService().apply_coupon(
            store=self.store, user=request.user, code=serializer.validated_data["code"]
        )
        return APIResponse.success(CartSerializer(cart).data, message="Coupon applied.")

    @extend_schema(responses=CartSerializer)
    def delete(self, request: Request) -> Response:
        cart = CartService().remove_coupon(store=self.store, user=request.user)
        return APIResponse.success(CartSerializer(cart).data, message="Coupon removed.")


@extend_schema(tags=["Orders"])
class CheckoutView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=CheckoutSerializer, responses=OrderSerializer)
    def post(self, request: Request) -> Response:
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = CheckoutService().checkout(
            store=self.store,
            user=request.user,
            shipping_method_id=serializer.validated_data.get("shipping_method_id"),
            country=serializer.validated_data.get("country") or "",
            currency=serializer.validated_data.get("currency") or "",
            address_id=serializer.validated_data.get("address_id"),
        )
        return APIResponse.success(
            OrderSerializer(order).data, message="Order placed.", status_code=201
        )


@extend_schema(tags=["Orders"])
class OrderListView(RequireStoreMixin, BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    filterset_fields = ("status",)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        return Order.objects.filter(user=self.request.user).prefetch_related("items")


@extend_schema(tags=["Orders"])
class OrderDetailView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def _get_order(self, request, order_id) -> Order:
        order = (
            Order.objects.filter(id=order_id, user=request.user).prefetch_related("items").first()
        )
        if order is None:
            raise NotFoundError("Order not found.")
        return order

    @extend_schema(responses=OrderSerializer)
    def get(self, request: Request, order_id) -> Response:
        order = self._get_order(request, order_id)
        return APIResponse.success(OrderSerializer(order).data)


@extend_schema(tags=["Orders"])
class OrderConfirmView(OrderDetailView):
    @extend_schema(request=None, responses=OrderSerializer)
    def post(self, request: Request, order_id) -> Response:
        order = self._get_order(request, order_id)
        order = CheckoutService().confirm_order(order=order)
        return APIResponse.success(OrderSerializer(order).data, message="Order confirmed.")


@extend_schema(tags=["Orders"])
class OrderCancelView(OrderDetailView):
    @extend_schema(request=None, responses=OrderSerializer)
    def post(self, request: Request, order_id) -> Response:
        order = self._get_order(request, order_id)
        order = CheckoutService().cancel_order(order=order)
        return APIResponse.success(OrderSerializer(order).data, message="Order cancelled.")


# --- Staff (store-scoped management) ---------------------------------------
@extend_schema(tags=["Orders"])
class OrderManageListView(StoreContextMixin, BaseGenericAPIView, generics.ListAPIView):
    """All orders for the current store (staff). Buyers use ``OrderListView``."""

    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    filterset_fields = ("status",)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        return Order.objects.filter(store=self.store).prefetch_related("items")


@extend_schema(tags=["Orders"])
class OrderManageDetailView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def _get_order(self, order_id) -> Order:
        order = (
            Order.objects.filter(id=order_id, store=self.store).prefetch_related("items").first()
        )
        if order is None:
            raise NotFoundError("Order not found.")
        return order

    @extend_schema(responses=OrderSerializer)
    def get(self, request: Request, order_id) -> Response:
        return APIResponse.success(OrderSerializer(self._get_order(order_id)).data)


@extend_schema(tags=["Orders"])
class OrderManageConfirmView(OrderManageDetailView):
    @extend_schema(request=None, responses=OrderSerializer)
    def post(self, request: Request, order_id) -> Response:
        self.require_write()
        order = CheckoutService().confirm_order(order=self._get_order(order_id))
        return APIResponse.success(OrderSerializer(order).data, message="Order confirmed.")


@extend_schema(tags=["Orders"])
class OrderManageCancelView(OrderManageDetailView):
    @extend_schema(request=None, responses=OrderSerializer)
    def post(self, request: Request, order_id) -> Response:
        self.require_write()
        order = CheckoutService().cancel_order(order=self._get_order(order_id))
        return APIResponse.success(OrderSerializer(order).data, message="Order cancelled.")
