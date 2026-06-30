"""Returns serializers."""

from __future__ import annotations

from rest_framework import serializers

from apps.returns.models import ReturnItem, ReturnRequest


class ReturnItemSerializer(serializers.ModelSerializer):
    sku = serializers.CharField(source="variant.sku", read_only=True)

    class Meta:
        model = ReturnItem
        fields = ("id", "order_item", "variant", "sku", "quantity", "reason")
        read_only_fields = fields


class ReturnRequestSerializer(serializers.ModelSerializer):
    items = ReturnItemSerializer(many=True, read_only=True)

    class Meta:
        model = ReturnRequest
        fields = (
            "id",
            "order",
            "status",
            "resolution",
            "reason",
            "refund_amount",
            "refund_reference",
            "processed_at",
            "items",
            "created_at",
        )
        read_only_fields = fields


class ReturnLineSerializer(serializers.Serializer):
    order_item_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class CreateReturnSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    reason = serializers.CharField(required=False, allow_blank=True, default="")
    resolution = serializers.ChoiceField(
        choices=["refund", "exchange", "store_credit"], default="refund"
    )
    items = ReturnLineSerializer(many=True, allow_empty=False)


class RejectReturnSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")
