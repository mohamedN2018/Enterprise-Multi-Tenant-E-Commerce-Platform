"""Analytics serializers."""

from __future__ import annotations

from rest_framework import serializers

from apps.analytics.models import AnalyticsEvent


class AnalyticsEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsEvent
        fields = ("id", "event_type", "user", "data", "occurred_at", "created_at")
        read_only_fields = fields


class SummaryQuerySerializer(serializers.Serializer):
    start = serializers.DateTimeField(required=False)
    end = serializers.DateTimeField(required=False)
