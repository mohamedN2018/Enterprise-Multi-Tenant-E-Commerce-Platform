"""Public storefront API (AllowAny): browse stores and their published catalog.

Cross-store and unauthenticated, so it uses the unscoped ``all_objects`` manager
with explicit ``is_deleted=False`` filters instead of the tenant-scoped default.
"""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.catalog.models import Product, ProductStatus
from apps.core.exceptions import NotFoundError
from apps.core.mixins import BaseAPIView, BaseGenericAPIView
from apps.core.responses import APIResponse
from apps.stores.models import Store, StoreStatus

from .serializers import (
    StorefrontProductDetailSerializer,
    StorefrontProductSerializer,
    StorefrontStoreSerializer,
)


def _active_store_or_404(slug: str) -> Store:
    store = Store.all_objects.filter(slug=slug, status=StoreStatus.ACTIVE, is_deleted=False).first()
    if store is None:
        raise NotFoundError("Store not found.")
    return store


@extend_schema(tags=["Storefront"])
class StorefrontStoreListView(BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = StorefrontStoreSerializer

    def get_queryset(self):
        return Store.all_objects.filter(status=StoreStatus.ACTIVE, is_deleted=False).order_by(
            "name"
        )


@extend_schema(tags=["Storefront"])
class StorefrontStoreDetailView(BaseAPIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=StorefrontStoreSerializer)
    def get(self, request: Request, slug: str) -> Response:
        store = _active_store_or_404(slug)
        return APIResponse.success(StorefrontStoreSerializer(store).data)


@extend_schema(tags=["Storefront"])
class StorefrontProductListView(BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = StorefrontProductSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Product.all_objects.none()
        store = _active_store_or_404(self.kwargs["slug"])
        return (
            Product.all_objects.filter(
                store=store, status=ProductStatus.PUBLISHED, is_deleted=False
            )
            .select_related("store")
            .prefetch_related("variants")
            .order_by("-created_at")
        )


@extend_schema(tags=["Storefront"])
class StorefrontProductDetailView(BaseAPIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=StorefrontProductDetailSerializer)
    def get(self, request: Request, product_id) -> Response:
        product = (
            Product.all_objects.filter(
                id=product_id, status=ProductStatus.PUBLISHED, is_deleted=False
            )
            .select_related("store")
            .prefetch_related("variants")
            .first()
        )
        if product is None:
            raise NotFoundError("Product not found.")
        return APIResponse.success(StorefrontProductDetailSerializer(product).data)
