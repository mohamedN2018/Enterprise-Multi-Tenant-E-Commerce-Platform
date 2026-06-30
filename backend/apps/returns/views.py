"""Returns API views (buyer RMA + staff processing)."""

from __future__ import annotations

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.core.mixins import BaseAPIView, BaseGenericAPIView
from apps.core.responses import APIResponse
from apps.returns.models import ReturnRequest
from apps.returns.serializers import (
    CreateReturnSerializer,
    RejectReturnSerializer,
    ReturnRequestSerializer,
)
from apps.returns.services import ReturnService
from apps.stores.context import RequireStoreMixin, StoreContextMixin


# --- Buyer -----------------------------------------------------------------
class ReturnListCreateView(RequireStoreMixin, BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReturnRequestSerializer
    filterset_fields = ("status",)

    def get_queryset(self):
        return ReturnRequest.objects.filter(user=self.request.user).prefetch_related("items")

    def post(self, request, *args, **kwargs):
        serializer = CreateReturnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        rma = ReturnService().create_return(
            store=self.store,
            user=request.user,
            order_id=data["order_id"],
            items=data["items"],
            reason=data["reason"],
            resolution=data["resolution"],
        )
        return APIResponse.success(
            ReturnRequestSerializer(rma).data, message="Return requested.", status_code=201
        )


class ReturnDetailView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, return_id):
        rma = ReturnService().get_for_user(user=request.user, return_id=return_id)
        return APIResponse.success(ReturnRequestSerializer(rma).data)


class ReturnCancelView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, return_id):
        service = ReturnService()
        rma = service.get_for_user(user=request.user, return_id=return_id)
        rma = service.cancel(rma=rma)
        return APIResponse.success(ReturnRequestSerializer(rma).data, message="Return cancelled.")


# --- Staff -----------------------------------------------------------------
class ReturnManageListView(StoreContextMixin, BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReturnRequestSerializer
    filterset_fields = ("status", "user")

    def get_queryset(self):
        return ReturnRequest.objects.all().prefetch_related("items")


class ReturnApproveView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, return_id):
        self.require_write()
        service = ReturnService()
        rma = service.approve(rma=service.get_for_store(return_id=return_id))
        return APIResponse.success(ReturnRequestSerializer(rma).data, message="Return approved.")


class ReturnRejectView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, return_id):
        self.require_write()
        serializer = RejectReturnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = ReturnService()
        rma = service.reject(
            rma=service.get_for_store(return_id=return_id),
            reason=serializer.validated_data["reason"],
        )
        return APIResponse.success(ReturnRequestSerializer(rma).data, message="Return rejected.")


class ReturnRefundView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, return_id):
        self.require_write()
        service = ReturnService()
        rma = service.refund(rma=service.get_for_store(return_id=return_id))
        return APIResponse.success(
            ReturnRequestSerializer(rma).data,
            message="Return refunded to wallet and items restocked.",
        )
