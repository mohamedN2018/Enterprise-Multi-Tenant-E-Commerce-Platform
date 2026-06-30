"""Pricing serializers."""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.pricing.models import CustomerGroup, CustomerGroupMembership, PriceRule

_ZERO = Decimal("0")


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
    rule_type = serializers.CharField(default="fixed")
    value = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=_ZERO)
    is_active = serializers.BooleanField(default=True)


class UpdatePriceRuleSerializer(serializers.Serializer):
    min_quantity = serializers.IntegerField(min_value=1, required=False)
    rule_type = serializers.CharField(required=False)
    value = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=_ZERO, required=False
    )
    is_active = serializers.BooleanField(required=False)
