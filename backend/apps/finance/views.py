"""Finance API views: tax zones/rates, currencies, exchange rates, conversion."""

from __future__ import annotations

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.core.exceptions import NotFoundError, ValidationError
from apps.core.mixins import BaseAPIView, BaseGenericAPIView
from apps.core.responses import APIResponse
from apps.finance.models import Currency, ExchangeRate, TaxZone
from apps.finance.serializers import (
    CreateExchangeRateSerializer,
    CurrencySerializer,
    ExchangeRateSerializer,
    TaxRateSerializer,
    TaxZoneSerializer,
)
from apps.finance.services import CurrencyService, TaxService
from apps.stores.context import RequireStoreMixin, StoreContextMixin


# --- Tax zones & rates (staff) ---------------------------------------------
class TaxZoneListCreateView(StoreContextMixin, BaseGenericAPIView, generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TaxZoneSerializer

    def get_queryset(self):
        return TaxZone.objects.all()

    def perform_create(self, serializer):
        self.require_write()
        serializer.instance = TaxService().create_zone(
            store=self.store, data=serializer.validated_data
        )


class TaxZoneDetailView(
    StoreContextMixin, BaseGenericAPIView, generics.RetrieveUpdateDestroyAPIView
):
    permission_classes = [IsAuthenticated]
    serializer_class = TaxZoneSerializer
    lookup_url_kwarg = "zone_id"

    def get_queryset(self):
        return TaxZone.objects.all()

    def perform_update(self, serializer):
        self.require_write()
        zone = serializer.save()
        if zone.is_default:
            TaxZone.objects.filter(store=self.store, is_default=True).exclude(pk=zone.pk).update(
                is_default=False
            )

    def perform_destroy(self, instance):
        self.require_write()
        instance.delete()


class TaxRateListCreateView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def _zone(self, zone_id) -> TaxZone:
        zone = TaxZone.objects.filter(id=zone_id).first()
        if zone is None:
            raise NotFoundError("Tax zone not found.")
        return zone

    def get(self, request, zone_id):
        zone = self._zone(zone_id)
        return APIResponse.success(TaxRateSerializer(TaxService().list_rates(zone), many=True).data)

    def post(self, request, zone_id):
        self.require_write()
        zone = self._zone(zone_id)
        serializer = TaxRateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rate = TaxService().add_rate(store=self.store, zone=zone, data=serializer.validated_data)
        return APIResponse.success(
            TaxRateSerializer(rate).data, message="Tax rate added.", status_code=201
        )


# --- Currencies (staff) ----------------------------------------------------
class CurrencyListCreateView(StoreContextMixin, BaseGenericAPIView, generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CurrencySerializer

    def get_queryset(self):
        return Currency.objects.all()

    def perform_create(self, serializer):
        self.require_write()
        serializer.instance = CurrencyService().create_currency(
            store=self.store, data=serializer.validated_data
        )


class ExchangeRateListCreateView(StoreContextMixin, BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExchangeRateSerializer
    filterset_fields = ("base_code", "target_code")

    def get_queryset(self):
        return ExchangeRate.objects.all()

    def post(self, request, *args, **kwargs):
        self.require_write()
        serializer = CreateExchangeRateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rate = CurrencyService().create_exchange_rate(
            store=self.store, data=serializer.validated_data
        )
        return APIResponse.success(
            ExchangeRateSerializer(rate).data, message="Exchange rate saved.", status_code=201
        )


# --- Conversion (any member) -----------------------------------------------
class ConvertView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        amount = request.query_params.get("amount")
        base_code = request.query_params.get("from")
        target_code = request.query_params.get("to")
        if not (amount and base_code and target_code):
            raise ValidationError(
                "'amount', 'from' and 'to' query parameters are required.",
                code="missing_parameters",
            )
        from decimal import Decimal, InvalidOperation

        try:
            amount_dec = Decimal(amount)
        except (InvalidOperation, TypeError):
            raise ValidationError("'amount' must be numeric.", code="invalid_amount") from None

        converted = CurrencyService().convert(
            store=self.store, amount=amount_dec, base_code=base_code, target_code=target_code
        )
        return APIResponse.success(
            data={
                "amount": str(amount_dec),
                "from": base_code.upper(),
                "to": target_code.upper(),
                "converted": str(converted),
            }
        )
