"""Serializers for the cashier integration (management + inbound sale)."""

from __future__ import annotations

from rest_framework import serializers

from apps.pos.models import PosConnection


class PosConnectionSerializer(serializers.ModelSerializer):
    """Safe read view — never exposes the key hash or webhook secret."""

    masked_key = serializers.SerializerMethodField()
    has_webhook = serializers.SerializerMethodField()

    class Meta:
        model = PosConnection
        fields = (
            "id",
            "name",
            "masked_key",
            "webhook_url",
            "has_webhook",
            "is_active",
            "last_used_at",
            "created_at",
        )
        read_only_fields = fields

    def get_masked_key(self, obj) -> str:
        return f"{obj.api_key_prefix}…"

    def get_has_webhook(self, obj) -> bool:
        return bool(obj.webhook_url)


class PosConnectionCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120, required=False, allow_blank=True, default="Cashier")
    webhook_url = serializers.URLField(required=False, allow_blank=True, default="")


class PosConnectionUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    webhook_url = serializers.URLField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)


class PosSaleLineSerializer(serializers.Serializer):
    sku = serializers.CharField(max_length=100)
    quantity = serializers.IntegerField(min_value=1)


class PosSaleSerializer(serializers.Serializer):
    items = PosSaleLineSerializer(many=True, allow_empty=False)
    reference = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
