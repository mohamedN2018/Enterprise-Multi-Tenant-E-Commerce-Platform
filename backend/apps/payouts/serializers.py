"""Payout serializers."""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.payouts.models import LedgerEntry, Payout, SellerAccount

_ZERO = Decimal("0")


class SellerAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerAccount
        fields = ("id", "balance", "currency", "commission_rate", "updated_at")
        read_only_fields = fields


class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = (
            "id",
            "entry_type",
            "order",
            "gross_amount",
            "commission_amount",
            "net_amount",
            "balance_after",
            "reference",
            "note",
            "created_at",
        )
        read_only_fields = fields


class PayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payout
        fields = ("id", "amount", "status", "reference", "paid_at", "created_at")
        read_only_fields = ("id", "status", "reference", "paid_at", "created_at")


class SetCommissionSerializer(serializers.Serializer):
    rate = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=_ZERO)


class RequestPayoutSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=_ZERO)
