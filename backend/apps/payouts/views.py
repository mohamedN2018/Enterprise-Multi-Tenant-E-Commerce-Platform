"""Payouts API (staff/seller): account, ledger, commission, payout requests."""

from __future__ import annotations

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.mixins import BaseAPIView, BaseGenericAPIView
from apps.core.permissions import IsSuperAdmin
from apps.core.responses import APIResponse
from apps.payouts.models import LedgerEntry, Payout
from apps.payouts.serializers import (
    LedgerEntrySerializer,
    PayoutSerializer,
    RequestPayoutSerializer,
    SellerAccountSerializer,
    SetCommissionSerializer,
)
from apps.payouts.services import PayoutService
from apps.stores.context import StoreContextMixin


def _validated(serializer_class, request) -> dict:
    serializer = serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


class SellerAccountView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        account = PayoutService().get_account(store=self.store)
        return APIResponse.success(SellerAccountSerializer(account).data)


class CommissionView(StoreContextMixin, BaseAPIView):
    # The platform's commission cut is a platform-level control, NOT something a
    # seller may set for their own store (rate=0 → seller keeps 100% of gross).
    # Restricted to super-admins; the target store comes from the X-Store-Id header.
    permission_classes = [IsSuperAdmin]

    def put(self, request: Request) -> Response:
        data = _validated(SetCommissionSerializer, request)
        account = PayoutService().set_commission_rate(store=self.store, rate=data["rate"])
        return APIResponse.success(
            SellerAccountSerializer(account).data, message="Commission rate updated."
        )


class LedgerListView(StoreContextMixin, BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LedgerEntrySerializer
    filterset_fields = ("entry_type",)

    def get_queryset(self):
        return LedgerEntry.objects.all()


class PayoutListCreateView(StoreContextMixin, BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PayoutSerializer
    filterset_fields = ("status",)

    def get_queryset(self):
        return Payout.objects.all()

    def post(self, request: Request, *args, **kwargs) -> Response:
        self.require_write()
        data = _validated(RequestPayoutSerializer, request)
        payout = PayoutService().request_payout(store=self.store, amount=data["amount"])
        return APIResponse.success(
            PayoutSerializer(payout).data, message="Payout requested.", status_code=201
        )


class PayoutMarkPaidView(StoreContextMixin, BaseAPIView):
    # Confirming a payout was actually disbursed is a platform action — a seller
    # must not be able to mark their own payout PAID. Super-admin only.
    permission_classes = [IsSuperAdmin]

    def post(self, request: Request, payout_id) -> Response:
        service = PayoutService()
        payout = service.mark_paid(payout=service.get_payout(store=self.store, payout_id=payout_id))
        return APIResponse.success(PayoutSerializer(payout).data, message="Payout marked paid.")
