"""Payment API views (buyer-facing)."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.exceptions import NotFoundError
from apps.core.mixins import BaseAPIView, BaseGenericAPIView
from apps.core.responses import APIResponse
from apps.orders.models import Order
from apps.payments.gateways import available_gateways
from apps.payments.models import Payment
from apps.payments.serializers import (
    CreatePaymentSerializer,
    GatewaySerializer,
    PaymentSerializer,
)
from apps.payments.services import PaymentService
from apps.stores.context import RequireStoreMixin


@extend_schema(tags=["Payments"])
class GatewayListView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=GatewaySerializer(many=True))
    def get(self, request: Request) -> Response:
        return APIResponse.success(GatewaySerializer(available_gateways(), many=True).data)


@extend_schema(tags=["Payments"])
class PaymentListCreateView(RequireStoreMixin, BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer
    filterset_fields = ("status", "gateway")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Payment.objects.none()
        return Payment.objects.filter(user=self.request.user)

    @extend_schema(request=CreatePaymentSerializer, responses=PaymentSerializer)
    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = CreatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = self._get_order(request, serializer.validated_data["order_id"])
        payment = PaymentService().create_payment(
            store=self.store,
            user=request.user,
            order=order,
            gateway_code=serializer.validated_data["gateway"],
        )
        return APIResponse.success(
            PaymentSerializer(payment).data, message="Payment initiated.", status_code=201
        )

    def _get_order(self, request, order_id) -> Order:
        order = Order.objects.filter(id=order_id, user=request.user).first()
        if order is None:
            raise NotFoundError("Order not found.")
        return order


@extend_schema(tags=["Payments"])
class PaymentDetailView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def _get_payment(self, request, payment_id) -> Payment:
        payment = Payment.objects.filter(id=payment_id, user=request.user).first()
        if payment is None:
            raise NotFoundError("Payment not found.")
        return payment

    @extend_schema(responses=PaymentSerializer)
    def get(self, request: Request, payment_id) -> Response:
        payment = self._get_payment(request, payment_id)
        return APIResponse.success(PaymentSerializer(payment).data)


@extend_schema(tags=["Payments"])
class PaymentCaptureView(PaymentDetailView):
    @extend_schema(request=None, responses=PaymentSerializer)
    def post(self, request: Request, payment_id) -> Response:
        payment = self._get_payment(request, payment_id)
        payment = PaymentService().capture_payment(payment=payment)
        return APIResponse.success(PaymentSerializer(payment).data, message="Payment captured.")
