"""Rewards serializers."""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.rewards.models import GiftCard, WalletTransaction

_ZERO = Decimal("0")


class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ("id", "txn_type", "amount", "balance_after", "reason", "reference", "created_at")
        read_only_fields = fields


class GiftCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = GiftCard
        fields = ("id", "code", "initial_balance", "balance", "status", "created_at")
        read_only_fields = fields


class IssueGiftCardSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=_ZERO)
    code = serializers.CharField(max_length=40, required=False, allow_blank=True)


class RedeemGiftCardSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=40)


class RedeemPointsSerializer(serializers.Serializer):
    points = serializers.IntegerField(min_value=1)
