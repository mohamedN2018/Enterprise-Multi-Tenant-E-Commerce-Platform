"""Catalog API views.

CRUD over tenant-scoped catalog resources. ``StoreContextMixin`` enforces an
active store context + membership; ``get_queryset`` runs through the tenant-aware
managers, so every list/lookup is implicitly isolated to the active store.
Writes route through :class:`CatalogService` and require manager/owner.
"""

from __future__ import annotations

from rest_framework import generics
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated

from apps.catalog.access import StoreContextMixin
from apps.catalog.models import Attribute, Brand, Category, DownloadGrant, Product, ProductVariant
from apps.catalog.serializers import (
    AddLicenseKeysSerializer,
    AddProductAttributeSerializer,
    AttributeSerializer,
    AttributeValueSerializer,
    BrandSerializer,
    BundleComponentCreateSerializer,
    BundleComponentSerializer,
    CategorySerializer,
    DigitalAssetSerializer,
    DownloadGrantSerializer,
    GenerateVariantsSerializer,
    LicenseKeySerializer,
    ProductAttributeSerializer,
    ProductSerializer,
    ProductVariantSerializer,
    SetVariantOptionsSerializer,
)
from apps.catalog.services import (
    AttributeService,
    BundleService,
    CatalogService,
    ConfigurableProductService,
    DigitalProductService,
    DownloadService,
)
from apps.core.exceptions import NotFoundError
from apps.core.mixins import BaseAPIView, BaseGenericAPIView
from apps.core.responses import APIResponse
from apps.stores.context import RequireStoreMixin


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
        qs = Product.objects.select_related("category", "brand").prefetch_related("variants").all()
        # Optional faceted filter: products having a variant with this option value.
        attribute_value = self.request.query_params.get("attribute_value")
        if attribute_value:
            qs = qs.filter(variants__option_values__attribute_value_id=attribute_value).distinct()
        return qs

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


class ProductImageView(StoreContextMixin, BaseAPIView):
    """Upload/replace or remove a product's primary image (multipart)."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def _get(self, product_id) -> Product:
        product = Product.objects.filter(id=product_id).first()
        if product is None:
            raise NotFoundError("Product not found.")
        return product

    def post(self, request, product_id):
        from apps.core.exceptions import ValidationError
        from apps.core.validators import validate_image_upload

        self.require_write()
        product = self._get(product_id)
        file = request.FILES.get("image")
        if file is None:
            raise ValidationError(
                "No image file provided.", code="no_image", errors={"image": ["An image is required."]}
            )
        validate_image_upload(file)
        product.image = file
        product.save(update_fields=["image", "updated_at"])
        return APIResponse.success(ProductSerializer(product, context={"request": request}).data,
                                   message="Image uploaded.")

    def delete(self, request, product_id):
        self.require_write()
        product = self._get(product_id)
        product.image.delete(save=False)
        product.image = None
        product.save(update_fields=["image", "updated_at"])
        return APIResponse.success(message="Image removed.")


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


# --- Bundle components (for bundle/kit/composite products) -----------------
class BundleComponentListCreateView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        bundle = BundleService().get_bundle(product_id=product_id)
        components = BundleService().list_components(bundle)
        return APIResponse.success(BundleComponentSerializer(components, many=True).data)

    def post(self, request, product_id):
        self.require_write()
        bundle = BundleService().get_bundle(product_id=product_id)
        serializer = BundleComponentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        component = BundleService().add_component(
            store=self.store, bundle=bundle, **serializer.validated_data
        )
        return APIResponse.success(
            BundleComponentSerializer(component).data,
            message="Component added.",
            status_code=201,
        )


class BundleComponentDetailView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, product_id, component_id):
        self.require_write()
        service = BundleService()
        bundle = service.get_bundle(product_id=product_id)
        component = service.get_component(bundle=bundle, component_id=component_id)
        service.remove_component(component=component)
        return APIResponse.success(message="Component removed.")


# --- Digital assets & license keys (staff) ---------------------------------
class DigitalAssetView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, variant_id):
        service = DigitalProductService()
        variant = service.get_variant(variant_id=variant_id)
        asset = service.get_asset(variant=variant)
        data = DigitalAssetSerializer(asset).data if asset else None
        return APIResponse.success(data=data)

    def put(self, request, variant_id):
        self.require_write()
        service = DigitalProductService()
        variant = service.get_variant(variant_id=variant_id)
        serializer = DigitalAssetSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        asset = service.upsert_asset(
            store=self.store, variant=variant, data=serializer.validated_data
        )
        return APIResponse.success(
            DigitalAssetSerializer(asset).data, message="Digital asset saved."
        )


class LicenseKeyListCreateView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, variant_id):
        service = DigitalProductService()
        variant = service.get_variant(variant_id=variant_id)
        keys = service.list_license_keys(variant=variant)
        return APIResponse.success(LicenseKeySerializer(keys, many=True).data)

    def post(self, request, variant_id):
        self.require_write()
        service = DigitalProductService()
        variant = service.get_variant(variant_id=variant_id)
        serializer = AddLicenseKeysSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        created = service.add_license_keys(
            store=self.store, variant=variant, keys=serializer.validated_data["keys"]
        )
        return APIResponse.success(
            LicenseKeySerializer(created, many=True).data,
            message=f"{len(created)} license key(s) added.",
            status_code=201,
        )


# --- Buyer downloads -------------------------------------------------------
class DownloadGrantListView(RequireStoreMixin, BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DownloadGrantSerializer

    def get_queryset(self):
        return DownloadGrant.objects.filter(user=self.request.user).select_related("digital_asset")


class DownloadView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, token):
        service = DownloadService()
        grant = service.get_grant(user=request.user, token=token)
        url = service.consume(grant=grant)
        grant.refresh_from_db()
        return APIResponse.success(
            data={
                "download_url": url,
                "download_count": grant.download_count,
                "remaining_downloads": grant.remaining_downloads,
            },
            message="Download authorized.",
        )


# --- Attributes & configurable products (staff) ----------------------------
class AttributeListCreateView(StoreContextMixin, BaseGenericAPIView, generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AttributeSerializer
    search_fields = ("name", "code")

    def get_queryset(self):
        return Attribute.objects.all()

    def perform_create(self, serializer):
        self.require_write()
        serializer.instance = AttributeService().create_attribute(
            store=self.store, data=serializer.validated_data
        )


class AttributeDetailView(
    StoreContextMixin, BaseGenericAPIView, generics.RetrieveUpdateDestroyAPIView
):
    permission_classes = [IsAuthenticated]
    serializer_class = AttributeSerializer
    lookup_url_kwarg = "attribute_id"

    def get_queryset(self):
        return Attribute.objects.all()

    def perform_update(self, serializer):
        self.require_write()
        serializer.instance = AttributeService().update_attribute(
            instance=serializer.instance, data=serializer.validated_data
        )

    def perform_destroy(self, instance):
        self.require_write()
        instance.delete()


class AttributeValueListCreateView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, attribute_id):
        service = AttributeService()
        attribute = service.get_attribute(attribute_id=attribute_id)
        return APIResponse.success(
            AttributeValueSerializer(service.list_values(attribute), many=True).data
        )

    def post(self, request, attribute_id):
        self.require_write()
        service = AttributeService()
        attribute = service.get_attribute(attribute_id=attribute_id)
        serializer = AttributeValueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        value = service.add_value(
            store=self.store, attribute=attribute, data=serializer.validated_data
        )
        return APIResponse.success(
            AttributeValueSerializer(value).data, message="Value added.", status_code=201
        )


class ProductAttributeListCreateView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def _product(self, product_id) -> Product:
        product = Product.objects.filter(id=product_id).first()
        if product is None:
            raise NotFoundError("Product not found.")
        return product

    def get(self, request, product_id):
        product = self._product(product_id)
        links = ConfigurableProductService().list_product_attributes(product)
        return APIResponse.success(ProductAttributeSerializer(links, many=True).data)

    def post(self, request, product_id):
        self.require_write()
        product = self._product(product_id)
        serializer = AddProductAttributeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        link = ConfigurableProductService().add_product_attribute(
            store=self.store,
            product=product,
            attribute_id=serializer.validated_data["attribute_id"],
        )
        return APIResponse.success(
            ProductAttributeSerializer(link).data, message="Attribute declared.", status_code=201
        )


class ProductAttributeDetailView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, product_id, product_attribute_id):
        self.require_write()
        product = Product.objects.filter(id=product_id).first()
        if product is None:
            raise NotFoundError("Product not found.")
        ConfigurableProductService().remove_product_attribute(
            product=product, product_attribute_id=product_attribute_id
        )
        return APIResponse.success(message="Attribute removed from product.")


class VariantOptionsView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def _variant(self, product_id, variant_id) -> ProductVariant:
        variant = (
            ProductVariant.objects.filter(id=variant_id, product_id=product_id)
            .select_related("product")
            .first()
        )
        if variant is None:
            raise NotFoundError("Variant not found.")
        return variant

    def get(self, request, product_id, variant_id):
        variant = self._variant(product_id, variant_id)
        options = variant.option_values.select_related("attribute", "attribute_value").all()
        data = [
            {
                "attribute": option.attribute.name,
                "value": option.attribute_value.label or option.attribute_value.value,
            }
            for option in options
        ]
        return APIResponse.success(data)

    def put(self, request, product_id, variant_id):
        self.require_write()
        variant = self._variant(product_id, variant_id)
        serializer = SetVariantOptionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ConfigurableProductService().set_variant_options(
            store=self.store,
            variant=variant,
            attribute_value_ids=serializer.validated_data["attribute_value_ids"],
        )
        return APIResponse.success(message="Variant options updated.")


class GenerateVariantMatrixView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def _product(self, product_id) -> Product:
        product = Product.objects.filter(id=product_id).first()
        if product is None:
            raise NotFoundError("Product not found.")
        return product

    def post(self, request, product_id):
        self.require_write()
        product = self._product(product_id)
        serializer = GenerateVariantsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        selections = None
        if data.get("selections"):
            selections = {
                str(key): [str(value) for value in values]
                for key, values in data["selections"].items()
            }
        variants = ConfigurableProductService().generate_variant_matrix(
            store=self.store,
            product=product,
            base_price=data["base_price"],
            sku_prefix=data.get("sku_prefix") or None,
            selections=selections,
        )
        return APIResponse.success(
            ProductVariantSerializer(variants, many=True).data,
            message=f"{len(variants)} variant(s) generated.",
            status_code=201,
        )
