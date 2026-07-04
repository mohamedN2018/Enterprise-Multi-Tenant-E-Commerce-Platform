"""Finance serializers."""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.finance.models import Currency, ExchangeRate, TaxRate, TaxZone


class TaxZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxZone
        fields = ("id", "name", "code", "countries", "is_default", "created_at")
        read_only_fields = ("id", "created_at")
        extra_kwargs = {"code": {"required": False}}


class TaxRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxRate
        fields = ("id", "name", "rate", "priority", "is_active", "created_at")
        read_only_fields = ("id", "created_at")
        # A negative tax rate would charge the buyer less than subtotal.
        extra_kwargs = {"rate": {"min_value": Decimal("0")}}


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ("id", "code", "name", "symbol", "is_active", "created_at")
        read_only_fields = ("id", "created_at")


class ExchangeRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRate
        fields = ("id", "base_code", "target_code", "rate", "created_at")
        read_only_fields = ("id", "created_at")


class CreateExchangeRateSerializer(serializers.Serializer):
    base_code = serializers.CharField(max_length=3)
    target_code = serializers.CharField(max_length=3)
    # Must be strictly positive — a zero/negative rate would settle a
    # foreign-currency order at (or below) zero.
    rate = serializers.DecimalField(
        max_digits=18, decimal_places=8, min_value=Decimal("0.00000001")
    )
