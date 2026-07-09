"""Shipping serializers."""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.shipping.models import ShippingMethod, ShippingZone


class ShippingZoneSerializer(serializers.ModelSerializer):
    is_geo = serializers.BooleanField(read_only=True)

    class Meta:
        model = ShippingZone
        fields = (
            "id", "name", "code", "countries", "is_default",
            "center_lat", "center_lng", "radius_km", "is_geo", "created_at",
        )
        read_only_fields = ("id", "is_geo", "created_at")
        extra_kwargs = {
            "code": {"required": False},
            "center_lat": {"min_value": Decimal("-90"), "max_value": Decimal("90")},
            "center_lng": {"min_value": Decimal("-180"), "max_value": Decimal("180")},
            "radius_km": {"min_value": Decimal("0.1"), "max_value": Decimal("2000")},
        }

    def validate(self, attrs):
        # A geo zone needs all three of centre lat/lng + radius, or none.
        merged = {**getattr(self, "initial_data", {}), **attrs}
        geo_vals = [merged.get("center_lat"), merged.get("center_lng"), merged.get("radius_km")]
        provided = [v for v in geo_vals if v not in (None, "")]
        if provided and len(provided) != 3:
            raise serializers.ValidationError(
                "A map zone needs a centre (lat & lng) and a radius in km."
            )
        return attrs


class ShippingMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingMethod
        fields = ("id", "zone", "name", "price", "per_kg", "free_over", "is_active", "created_at")
        read_only_fields = ("id", "zone", "created_at")
        # Shipping charges cannot be negative — a negative price/per_kg would
        # reduce the order total below subtotal.
        extra_kwargs = {
            "price": {"min_value": Decimal("0")},
            "per_kg": {"min_value": Decimal("0")},
            "free_over": {"min_value": Decimal("0")},
        }


class AvailableMethodSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source="zone.name", read_only=True)

    class Meta:
        model = ShippingMethod
        fields = ("id", "name", "price", "per_kg", "free_over", "zone_name")
        read_only_fields = fields


class SetTrackingSerializer(serializers.Serializer):
    tracking_number = serializers.CharField(max_length=120)
