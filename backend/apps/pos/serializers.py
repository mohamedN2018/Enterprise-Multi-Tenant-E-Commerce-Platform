"""Serializers for the cashier integration (management + inbound sale)."""

from __future__ import annotations

from rest_framework import serializers

from apps.pos.models import PosConnection, PosSupplierConnection


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


# --- Outbound supplier (import products from an external POS) ---
class PosSupplierSerializer(serializers.ModelSerializer):
    """Safe read view — never exposes the stored supplier API key."""

    has_key = serializers.SerializerMethodField()

    class Meta:
        model = PosSupplierConnection
        fields = (
            "id",
            "provider",
            "api_url",
            "is_connected",
            "has_key",
            "remote_store_name",
            "remote_product_count",
            "last_verified_at",
            "last_synced_at",
            "last_import_created",
            "last_import_updated",
        )
        read_only_fields = fields

    def get_has_key(self, obj) -> bool:
        return bool(obj.api_key)


class PosSupplierConnectSerializer(serializers.Serializer):
    provider = serializers.CharField(max_length=80, required=False, allow_blank=True, default="q-shop POS")
    api_url = serializers.URLField()
    api_key = serializers.CharField(max_length=255, trim_whitespace=True)
