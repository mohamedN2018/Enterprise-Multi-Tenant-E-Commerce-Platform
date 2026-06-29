"""Promotions serializers."""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.promotions.models import Coupon, DiscountType


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
