"""Catalog serializers.

Related fields (``parent``/``category``/``brand``) resolve their querysets from
the tenant-scoped default manager, so a payload can only reference objects that
belong to the active store — cross-store references are rejected automatically.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.catalog.models import (
    Attribute,
    AttributeValue,
    Brand,
    BundleComponent,
    Category,
    DigitalAsset,
    DownloadGrant,
    LicenseKey,
    Product,
    ProductAttribute,
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
    option_values = serializers.SerializerMethodField()

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
            "option_values",
            "is_default",
            "position",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "product", "created_at", "updated_at")

    def get_option_values(self, obj) -> list:
        return [
            {
                "attribute": option.attribute.name,
                "value": option.attribute_value.label or option.attribute_value.value,
            }
            for option in obj.option_values.all()
        ]


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
    product_attributes = serializers.SerializerMethodField()

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
            "product_attributes",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "slug",
            "published_at",
            "variants",
            "components",
            "product_attributes",
            "created_at",
            "updated_at",
        )

    def get_product_attributes(self, obj) -> list:
        return [
            {"id": str(pa.id), "attribute": pa.attribute.name, "code": pa.attribute.code}
            for pa in obj.product_attributes.all()
        ]


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


# --- Configurable products & attributes ------------------------------------
class AttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attribute
        fields = ("id", "name", "code", "is_variant", "sort_order", "created_at")
        read_only_fields = ("id", "created_at")
        extra_kwargs = {"code": {"required": False}}


class AttributeValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeValue
        fields = ("id", "value", "label", "sort_order", "created_at")
        read_only_fields = ("id", "created_at")


class ProductAttributeSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source="attribute.name", read_only=True)
    attribute_code = serializers.CharField(source="attribute.code", read_only=True)

    class Meta:
        model = ProductAttribute
        fields = ("id", "attribute", "attribute_name", "attribute_code", "sort_order")
        read_only_fields = fields


class AddProductAttributeSerializer(serializers.Serializer):
    attribute_id = serializers.UUIDField()


class SetVariantOptionsSerializer(serializers.Serializer):
    attribute_value_ids = serializers.ListField(child=serializers.UUIDField(), allow_empty=True)
