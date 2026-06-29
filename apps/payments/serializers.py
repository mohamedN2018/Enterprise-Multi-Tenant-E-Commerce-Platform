"""Payment serializers."""

from __future__ import annotations

from rest_framework import serializers

from apps.payments.models import Payment


class GatewaySerializer(serializers.Serializer):
    code = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "order",
            "gateway",
            "amount",
            "currency",
            "status",
            "transaction_id",
            "redirect_url",
            "error_message",
            "paid_at",
            "created_at",
        )
        read_only_fields = fields


class CreatePaymentSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    gateway = serializers.CharField(max_length=32)
