"""Reusable serializer bases."""
from __future__ import annotations

from rest_framework import serializers


class TimestampedSerializerMixin(serializers.Serializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class BaseModelSerializer(serializers.ModelSerializer):
    """ModelSerializer with audit/identity fields locked read-only by default."""

    class Meta:
        abstract = True
        read_only_fields = ("id", "created_at", "updated_at")
