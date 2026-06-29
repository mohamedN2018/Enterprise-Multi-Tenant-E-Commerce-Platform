"""Catalog serializers.

Related fields (``parent``/``category``/``brand``) resolve their querysets from
the tenant-scoped default manager, so a payload can only reference objects that
belong to the active store — cross-store references are rejected automatically.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.catalog.models import (
    Brand,
    BundleComponent,
    Category,
    DigitalAsset,
    DownloadGrant,
    LicenseKey,
    Product,
    ProductVariant,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
            "parent",
            "description",
            "is_active",
            "position",
            "meta_title",
            "meta_description",
            "meta_keywords",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at")


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "meta_title",
            "meta_description",
            "meta_keywords",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at")


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "product",
            "name",
            "sku",
            "barcode",
            "price",
            "compare_at_price",
            "cost_price",
            "stock_quantity",
            "track_inventory",
            "weight",
            "options",
            "is_default",
            "position",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "product", "created_at", "updated_at")


class BundleComponentSerializer(serializers.ModelSerializer):
    component_sku = serializers.CharField(source="component_variant.sku", read_only=True)

    class Meta:
        model = BundleComponent
        fields = (
            "id",
            "component_variant",
            "component_sku",
            "quantity",
            "is_optional",
            "sort_order",
        )
        read_only_fields = fields


class BundleComponentCreateSerializer(serializers.Serializer):
    component_variant_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    is_optional = serializers.BooleanField(default=False)
    sort_order = serializers.IntegerField(min_value=0, default=0)


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    components = BundleComponentSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "category",
            "brand",
            "product_type",
            "kind",
            "status",
            "is_active",
            "published_at",
            "meta_title",
            "meta_description",
            "meta_keywords",
            "variants",
            "components",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "slug",
            "published_at",
            "variants",
            "components",
            "created_at",
            "updated_at",
        )


class DigitalAssetSerializer(serializers.ModelSerializer):
    download_url = serializers.CharField(read_only=True)

    class Meta:
        model = DigitalAsset
        fields = (
            "id",
            "variant",
            "name",
            "file",
            "external_url",
            "download_url",
            "download_limit",
            "download_expiry_days",
            "requires_license",
            "is_active",
            "updated_at",
        )
        read_only_fields = ("id", "variant", "download_url", "updated_at")


class LicenseKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = LicenseKey
        fields = ("id", "key", "status", "assigned_at", "created_at")
        read_only_fields = fields


class AddLicenseKeysSerializer(serializers.Serializer):
    keys = serializers.ListField(child=serializers.CharField(max_length=255), allow_empty=False)


class DownloadGrantSerializer(serializers.ModelSerializer):
    remaining_downloads = serializers.SerializerMethodField()
    can_download = serializers.SerializerMethodField()
    license_keys = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = DownloadGrant
        fields = (
            "id",
            "order",
            "variant",
            "token",
            "download_url",
            "download_limit",
            "download_count",
            "remaining_downloads",
            "expires_at",
            "can_download",
            "license_keys",
            "created_at",
        )
        read_only_fields = fields

    def get_remaining_downloads(self, obj):
        return obj.remaining_downloads

    def get_can_download(self, obj) -> bool:
        return obj.can_download()

    def get_download_url(self, obj) -> str:
        return obj.digital_asset.download_url if obj.digital_asset else ""

    def get_license_keys(self, obj) -> list[str]:
        from apps.catalog.models import LicenseKeyStatus

        return list(
            LicenseKey.objects.filter(
                assigned_order=obj.order,
                variant=obj.variant,
                assigned_user=obj.user,
                status=LicenseKeyStatus.ASSIGNED,
            ).values_list("key", flat=True)
        )
