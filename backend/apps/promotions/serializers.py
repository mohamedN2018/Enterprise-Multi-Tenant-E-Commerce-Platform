"""Promotions serializers."""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.promotions.models import (
    Campaign,
    CampaignProduct,
    CampaignType,
    Coupon,
    DiscountType,
)


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = (
            "id",
            "code",
            "description",
            "discount_type",
            "value",
            "min_spend",
            "max_discount",
            "usage_limit",
            "per_user_limit",
            "used_count",
            "starts_at",
            "ends_at",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "used_count", "created_at", "updated_at")

    def validate_value(self, value: Decimal) -> Decimal:
        if value <= 0:
            raise serializers.ValidationError("Discount value must be positive.")
        return value

    def validate(self, attrs: dict) -> dict:
        discount_type = attrs.get("discount_type") or getattr(self.instance, "discount_type", None)
        value = attrs.get("value", getattr(self.instance, "value", None))
        if discount_type == DiscountType.PERCENTAGE and value is not None and value > 100:
            raise serializers.ValidationError({"value": "Percentage discount cannot exceed 100."})
        starts_at = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        ends_at = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        if starts_at and ends_at and ends_at < starts_at:
            raise serializers.ValidationError({"ends_at": "End date must be after the start date."})
        return attrs


class ApplyCouponSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=64)


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = (
            "id",
            "name",
            "description",
            "campaign_type",
            "discount_type",
            "discount_value",
            "max_discount",
            "min_spend",
            "buy_quantity",
            "get_quantity",
            "get_discount_percent",
            "priority",
            "stackable",
            "starts_at",
            "ends_at",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def _get(self, attrs: dict, name: str):
        return attrs.get(name, getattr(self.instance, name, None))

    def validate(self, attrs: dict) -> dict:
        campaign_type = self._get(attrs, "campaign_type")
        starts_at = self._get(attrs, "starts_at")
        ends_at = self._get(attrs, "ends_at")
        if starts_at and ends_at and ends_at < starts_at:
            raise serializers.ValidationError({"ends_at": "End date must be after the start date."})

        if campaign_type in (CampaignType.FLASH_SALE, CampaignType.ORDER_DISCOUNT):
            discount_type = self._get(attrs, "discount_type")
            discount_value = self._get(attrs, "discount_value")
            if not discount_type:
                raise serializers.ValidationError(
                    {"discount_type": "Required for this campaign type."}
                )
            if discount_value is None or discount_value <= 0:
                raise serializers.ValidationError(
                    {"discount_value": "A positive discount value is required."}
                )
            if discount_type == DiscountType.PERCENTAGE and discount_value > 100:
                raise serializers.ValidationError(
                    {"discount_value": "Percentage discount cannot exceed 100."}
                )
        elif campaign_type == CampaignType.BUY_X_GET_Y:
            for f in ("buy_quantity", "get_quantity"):
                if not self._get(attrs, f):
                    raise serializers.ValidationError({f: "Required and must be positive."})
            percent = self._get(attrs, "get_discount_percent")
            if percent is None or not (0 < percent <= 100):
                raise serializers.ValidationError(
                    {"get_discount_percent": "Must be between 0 and 100."}
                )
        return attrs


class CampaignProductSerializer(serializers.ModelSerializer):
    product = serializers.UUIDField(source="product_id")
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = CampaignProduct
        fields = ("id", "product", "product_name", "created_at")
        read_only_fields = ("id", "product_name", "created_at")
