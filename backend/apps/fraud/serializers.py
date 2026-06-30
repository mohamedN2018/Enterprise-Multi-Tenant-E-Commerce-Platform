"""Fraud serializers."""

from __future__ import annotations

from rest_framework import serializers

from apps.fraud.models import FraudCheck


class FraudCheckSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source="order.number", read_only=True)
    order_total = serializers.DecimalField(
        source="order.total", max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = FraudCheck
        fields = (
            "id",
            "order",
            "order_number",
            "order_total",
            "score",
            "decision",
            "resolution",
            "reasons",
            "reviewed_at",
            "created_at",
        )
        read_only_fields = fields
