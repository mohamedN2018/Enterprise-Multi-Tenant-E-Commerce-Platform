"""Catalog API views.

CRUD over tenant-scoped catalog resources. ``StoreContextMixin`` enforces an
active store context + membership; ``get_queryset`` runs through the tenant-aware
managers, so every list/lookup is implicitly isolated to the active store.
Writes route through :class:`CatalogService` and require manager/owner.
"""

from __future__ import annotations

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.catalog.access import StoreContextMixin
from apps.catalog.models import Brand, Category, Product, ProductVariant
from apps.catalog.serializers import (
    BrandSerializer,
    CategorySerializer,
    ProductSerializer,
    ProductVariantSerializer,
)
from apps.catalog.services import CatalogService
from apps.core.exceptions import NotFoundError
from apps.core.mixins import BaseGenericAPIView


# --- Category --------------------------------------------------------------
class CategoryListCreateView(StoreContextMixin, BaseGenericAPIView, generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer
    search_fields = ("name",)
    filterset_fields = ("is_active", "parent")

    def get_queryset(self):
        return Category.objects.all()

    def perform_create(self, serializer):
        self.require_write()
        serializer.instance = CatalogService().create_category(
            store=self.store, data=serializer.validated_data
        )


class CategoryDetailView(
    StoreContextMixin, BaseGenericAPIView, generics.RetrieveUpdateDestroyAPIView
):
    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer
    lookup_url_kwarg = "category_id"

    def get_queryset(self):
        return Category.objects.all()

    def perform_update(self, serializer):
        self.require_write()
        serializer.instance = CatalogService().update_category(
            instance=serializer.instance, data=serializer.validated_data
        )

    def perform_destroy(self, instance):
        self.require_write()
        instance.delete()


# --- Brand -----------------------------------------------------------------
class BrandListCreateView(StoreContextMixin, BaseGenericAPIView, generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BrandSerializer
    search_fields = ("name",)
    filterset_fields = ("is_active",)

    def get_queryset(self):
        return Brand.objects.all()

    def perform_create(self, serializer):
        self.require_write()
        serializer.instance = CatalogService().create_brand(
            store=self.store, data=serializer.validated_data
        )


class BrandDetailView(StoreContextMixin, BaseGenericAPIView, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BrandSerializer
    lookup_url_kwarg = "brand_id"

    def get_queryset(self):
        return Brand.objects.all()

    def perform_update(self, serializer):
        self.require_write()
        serializer.instance = CatalogService().update_brand(
            instance=serializer.instance, data=serializer.validated_data
        )

    def perform_destroy(self, instance):
        self.require_write()
        instance.delete()


# --- Product ---------------------------------------------------------------
class ProductListCreateView(StoreContextMixin, BaseGenericAPIView, generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer
    search_fields = ("name", "description")
    filterset_fields = ("status", "category", "brand", "product_type", "is_active")
    ordering_fields = ("created_at", "name")

    def get_queryset(self):
        return (
            Product.objects.select_related("category", "brand").prefetch_related("variants").all()
        )

    def perform_create(self, serializer):
        self.require_write()
        serializer.instance = CatalogService().create_product(
            store=self.store, data=serializer.validated_data
        )


class ProductDetailView(
    StoreContextMixin, BaseGenericAPIView, generics.RetrieveUpdateDestroyAPIView
):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer
    lookup_url_kwarg = "product_id"

    def get_queryset(self):
        return Product.objects.select_related("category", "brand").prefetch_related("variants")

    def perform_update(self, serializer):
        self.require_write()
        serializer.instance = CatalogService().update_product(
            instance=serializer.instance, data=serializer.validated_data
        )

    def perform_destroy(self, instance):
        self.require_write()
        instance.delete()


# --- Variant (nested under product) ---------------------------------------
class VariantListCreateView(StoreContextMixin, BaseGenericAPIView, generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductVariantSerializer

    def _get_product(self) -> Product:
        product = Product.objects.filter(id=self.kwargs["product_id"]).first()
        if product is None:
            raise NotFoundError("Product not found.")
        return product

    def get_queryset(self):
        return ProductVariant.objects.filter(product_id=self.kwargs["product_id"])

    def perform_create(self, serializer):
        self.require_write()
        product = self._get_product()
        serializer.instance = CatalogService().create_variant(
            store=self.store, product=product, data=serializer.validated_data
        )


class VariantDetailView(
    StoreContextMixin, BaseGenericAPIView, generics.RetrieveUpdateDestroyAPIView
):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductVariantSerializer
    lookup_url_kwarg = "variant_id"

    def get_queryset(self):
        return ProductVariant.objects.filter(product_id=self.kwargs["product_id"])

    def perform_update(self, serializer):
        self.require_write()
        serializer.instance = CatalogService().update_variant(
            instance=serializer.instance, data=serializer.validated_data
        )

    def perform_destroy(self, instance):
        self.require_write()
        instance.delete()
