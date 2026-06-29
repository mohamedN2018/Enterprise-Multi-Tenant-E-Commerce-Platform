"""Fraud review API (staff): the review queue + clear / reject actions."""

from __future__ import annotations

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.exceptions import NotFoundError
from apps.core.mixins import BaseAPIView, BaseGenericAPIView
from apps.core.responses import APIResponse
from apps.fraud.models import FraudCheck
from apps.fraud.serializers import FraudCheckSerializer
from apps.fraud.services import FraudService
from apps.stores.context import StoreContextMixin


class FraudCheckListView(StoreContextMixin, BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FraudCheckSerializer
    filterset_fields = ("decision", "resolution")

    def get_queryset(self):
        return FraudCheck.objects.select_related("order").all()


class FraudCheckDetailView(StoreContextMixin, BaseGenericAPIView, generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FraudCheckSerializer
    lookup_url_kwarg = "check_id"

    def get_queryset(self):
        return FraudCheck.objects.select_related("order").all()


class _FraudActionView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]
    action = ""
    message = ""

    def _get_check(self) -> FraudCheck:
        check = FraudCheck.objects.filter(id=self.kwargs["check_id"]).first()
        if check is None:
            raise NotFoundError("Fraud check not found.")
        return check

    def post(self, request: Request, check_id) -> Response:
        self.require_write()
        method = getattr(FraudService(), self.action)
        check = method(check=self._get_check(), reviewer=request.user)
        return APIResponse.success(FraudCheckSerializer(check).data, message=self.message)


class FraudCheckClearView(_FraudActionView):
    action = "clear"
    message = "Order cleared for fulfilment."


class FraudCheckRejectView(_FraudActionView):
    action = "reject"
    message = "Order rejected and cancelled."
