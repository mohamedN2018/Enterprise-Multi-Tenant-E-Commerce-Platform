"""Promotions API: coupon management (staff) + campaigns (staff CRUD, buyer read)."""

from __future__ import annotations

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.catalog.models import Product
from apps.core.exceptions import NotFoundError
from apps.core.mixins import BaseGenericAPIView
from apps.promotions.models import Campaign, CampaignProduct, Coupon
from apps.promotions.serializers import (
    CampaignProductSerializer,
    CampaignSerializer,
    CouponSerializer,
)
from apps.promotions.services import CampaignService, PromotionService
from apps.stores.context import RequireStoreMixin, StoreContextMixin


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


class CampaignListCreateView(StoreContextMixin, BaseGenericAPIView, generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CampaignSerializer
    search_fields = ("name", "description")
    filterset_fields = ("campaign_type", "is_active")

    def get_queryset(self):
        return Campaign.objects.all()

    def perform_create(self, serializer):
        self.require_write()
        serializer.instance = CampaignService().create_campaign(
            store=self.store, data=serializer.validated_data
        )


class CampaignDetailView(
    StoreContextMixin, BaseGenericAPIView, generics.RetrieveUpdateDestroyAPIView
):
    permission_classes = [IsAuthenticated]
    serializer_class = CampaignSerializer
    lookup_url_kwarg = "campaign_id"

    def get_queryset(self):
        return Campaign.objects.all()

    def perform_update(self, serializer):
        self.require_write()
        serializer.instance = CampaignService().update_campaign(
            instance=serializer.instance, data=serializer.validated_data
        )

    def perform_destroy(self, instance):
        self.require_write()
        instance.delete()


class CampaignProductListCreateView(
    StoreContextMixin, BaseGenericAPIView, generics.ListCreateAPIView
):
    permission_classes = [IsAuthenticated]
    serializer_class = CampaignProductSerializer

    def _campaign(self) -> Campaign:
        return CampaignService().get_campaign(
            store=self.store, campaign_id=self.kwargs["campaign_id"]
        )

    def get_queryset(self):
        return CampaignService().list_products(campaign=self._campaign())

    def perform_create(self, serializer):
        self.require_write()
        product = Product.objects.filter(
            store=self.store, id=serializer.validated_data["product_id"]
        ).first()
        if product is None:
            raise NotFoundError("Product not found.")
        serializer.instance = CampaignService().add_product(
            store=self.store, campaign=self._campaign(), product=product
        )


class CampaignProductDetailView(StoreContextMixin, BaseGenericAPIView, generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CampaignProductSerializer
    lookup_url_kwarg = "link_id"

    def get_queryset(self):
        return CampaignProduct.objects.filter(campaign_id=self.kwargs["campaign_id"])

    def perform_destroy(self, instance):
        self.require_write()
        instance.delete()


class ActiveCampaignListView(RequireStoreMixin, BaseGenericAPIView, generics.ListAPIView):
    """Buyer-facing list of currently live campaigns in the store."""

    permission_classes = [IsAuthenticated]
    serializer_class = CampaignSerializer
    pagination_class = None

    def get_queryset(self):
        return CampaignService().active_campaigns(store=self.store)
