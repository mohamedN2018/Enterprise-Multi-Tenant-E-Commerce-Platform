"""Shipping serializers."""

from __future__ import annotations

from rest_framework import serializers

from apps.shipping.models import ShippingMethod, ShippingZone


class ShippingZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingZone
        fields = ("id", "name", "code", "countries", "is_default", "created_at")
        read_only_fields = ("id", "created_at")
        extra_kwargs = {"code": {"required": False}}


class ShippingMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingMethod
        fields = ("id", "zone", "name", "price", "per_kg", "free_over", "is_active", "created_at")
        read_only_fields = ("id", "zone", "created_at")


class AvailableMethodSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source="zone.name", read_only=True)

    class Meta:
        model = ShippingMethod
        fields = ("id", "name", "price", "per_kg", "free_over", "zone_name")
        read_only_fields = fields


class SetTrackingSerializer(serializers.Serializer):
    tracking_number = serializers.CharField(max_length=120)
