"""Address serializers."""

from __future__ import annotations

from rest_framework import serializers

from apps.addresses.models import Address


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = (
            "id",
            "label",
            "full_name",
            "line1",
            "line2",
            "city",
            "region",
            "postal_code",
            "country",
            "phone",
            "lat",
            "lng",
            "is_default",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
