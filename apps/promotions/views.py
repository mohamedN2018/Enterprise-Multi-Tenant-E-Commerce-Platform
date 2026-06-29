"""Coupon management API (staff)."""

from __future__ import annotations

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.core.mixins import BaseGenericAPIView
from apps.promotions.models import Coupon
from apps.promotions.serializers import CouponSerializer
from apps.promotions.services import PromotionService
from apps.stores.context import StoreContextMixin


class CouponListCreateView(StoreContextMixin, BaseGenericAPIView, generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CouponSerializer
    search_fields = ("code", "description")
    filterset_fields = ("is_active", "discount_type")

    def get_queryset(self):
        return Coupon.objects.all()

    def perform_create(self, serializer):
        self.require_write()
        serializer.instance = PromotionService().create_coupon(
            store=self.store, data=serializer.validated_data
        )


class CouponDetailView(
    StoreContextMixin, BaseGenericAPIView, generics.RetrieveUpdateDestroyAPIView
):
    permission_classes = [IsAuthenticated]
    serializer_class = CouponSerializer
    lookup_url_kwarg = "coupon_id"

    def get_queryset(self):
        return Coupon.objects.all()

    def perform_update(self, serializer):
        self.require_write()
        serializer.instance = PromotionService().update_coupon(
            instance=serializer.instance, data=serializer.validated_data
        )

    def perform_destroy(self, instance):
        self.require_write()
        instance.delete()
