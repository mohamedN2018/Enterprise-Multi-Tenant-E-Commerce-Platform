"""Pricing serializers."""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.pricing.models import (
    CustomerGroup,
    CustomerGroupMembership,
    PriceRule,
    PriceRuleType,
)

_ZERO = Decimal("0")
_HUNDRED = Decimal("100")


def _validate_percent_within_bounds(attrs: dict) -> dict:
    """A percentage discount above 100% would resolve to a negative price."""
    if attrs.get("rule_type") == PriceRuleType.PERCENT_DISCOUNT:
        value = attrs.get("value")
        if value is not None and value > _HUNDRED:
            raise serializers.ValidationError(
                {"value": "A percentage discount cannot exceed 100%."}
            )
    return attrs


class CustomerGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerGroup
        fields = ("id", "name", "code", "description", "is_default", "priority", "created_at")
        read_only_fields = ("id", "created_at")
        extra_kwargs = {"code": {"required": False}}


class CustomerGroupMembershipSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = CustomerGroupMembership
        fields = ("id", "user", "user_email", "created_at")
        read_only_fields = fields


class AssignMemberSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PriceRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceRule
        fields = (
            "id",
            "variant",
            "customer_group",
            "min_quantity",
            "rule_type",
            "value",
            "is_active",
            "created_at",
        )
        read_only_fields = fields


class CreatePriceRuleSerializer(serializers.Serializer):
    variant_id = serializers.UUIDField()
    customer_group_id = serializers.UUIDField(required=False, allow_null=True)
    min_quantity = serializers.IntegerField(min_value=1, default=1)
    rule_type = serializers.ChoiceField(
        choices=PriceRuleType.choices, default=PriceRuleType.FIXED
    )
    value = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=_ZERO)
    is_active = serializers.BooleanField(default=True)

    def validate(self, attrs):
        return _validate_percent_within_bounds(attrs)


class UpdatePriceRuleSerializer(serializers.Serializer):
    min_quantity = serializers.IntegerField(min_value=1, required=False)
    rule_type = serializers.ChoiceField(choices=PriceRuleType.choices, required=False)
    value = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=_ZERO, required=False
    )
    is_active = serializers.BooleanField(required=False)

    def validate(self, attrs):
        return _validate_percent_within_bounds(attrs)
