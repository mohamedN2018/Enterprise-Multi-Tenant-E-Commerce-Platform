"""Finance services: tax-rate resolution + currency conversion."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Sum
from django.utils.text import slugify

from apps.core.exceptions import BusinessRuleError, ConflictError
from apps.core.services import BaseService, atomic
from apps.finance.models import Currency, ExchangeRate, TaxRate, TaxZone
from apps.finance.repositories import (
    CurrencyRepository,
    ExchangeRateRepository,
    TaxZoneRepository,
)

_CENTS = Decimal("0.01")


def _money(value) -> Decimal:
    return Decimal(value).quantize(_CENTS, rounding=ROUND_HALF_UP)


class TaxService(BaseService):
    def __init__(self, zone_repo: TaxZoneRepository | None = None) -> None:
        self.zone_repo = zone_repo or TaxZoneRepository()

    def resolve_rate(self, *, store, country: str | None = None) -> Decimal:
        """Combined active tax percentage for the matching zone.

        Falls back to the store's flat ``default_tax_rate`` when no zone matches
        (preserving pre-tax-engine behaviour).
        """
        zone = self._zone_for(store=store, country=country)
        if zone is not None:
            total = TaxRate.objects.filter(zone=zone, is_active=True).aggregate(total=Sum("rate"))[
                "total"
            ]
            if total is not None:
                return total
        return store.settings.default_tax_rate or Decimal("0")

    def _zone_for(self, *, store, country: str | None) -> TaxZone | None:
        zones = TaxZone.objects.filter(store=store)
        if country:
            for zone in zones:
                if zone.covers(country):
                    return zone
        return zones.filter(is_default=True).first()

    # --- Management ---
    @atomic
    def create_zone(self, *, store, data: dict) -> TaxZone:
        code = data.get("code")
        if code:
            if self.zone_repo.code_exists(store=store, code=code):
                raise ConflictError("A tax zone with this code already exists.", code="code_taken")
        else:
            code = self._unique_code(store=store, name=data["name"])
        payload = {k: v for k, v in data.items() if k != "code"}
        zone = TaxZone.objects.create(store=store, code=code, **payload)
        if zone.is_default:
            TaxZone.objects.filter(store=store, is_default=True).exclude(pk=zone.pk).update(
                is_default=False
            )
        return zone

    def list_rates(self, zone: TaxZone):
        return zone.rates.all()

    @atomic
    def add_rate(self, *, store, zone: TaxZone, data: dict) -> TaxRate:
        return TaxRate.objects.create(store=store, zone=zone, **data)

    def _unique_code(self, *, store, name: str) -> str:
        base = slugify(name)[:110] or "zone"
        code = base
        suffix = 1
        while self.zone_repo.code_exists(store=store, code=code):
            suffix += 1
            code = f"{base}-{suffix}"
        return code


class CurrencyService(BaseService):
    def __init__(self, currency_repo: CurrencyRepository | None = None) -> None:
        self.currency_repo = currency_repo or CurrencyRepository()
        self.rate_repo = ExchangeRateRepository()

    def convert(self, *, store, amount, base_code: str, target_code: str) -> Decimal:
        base_code = base_code.upper()
        target_code = target_code.upper()
        if base_code == target_code:
            return _money(amount)
        rate = ExchangeRate.objects.filter(
            store=store, base_code=base_code, target_code=target_code
        ).first()
        if rate is not None:
            return _money(Decimal(amount) * rate.rate)
        inverse = ExchangeRate.objects.filter(
            store=store, base_code=target_code, target_code=base_code
        ).first()
        if inverse is not None and inverse.rate != 0:
            return _money(Decimal(amount) / inverse.rate)
        raise BusinessRuleError(
            "No exchange rate configured for this currency pair.", code="no_exchange_rate"
        )

    @atomic
    def create_currency(self, *, store, data: dict) -> Currency:
        code = data["code"].strip().upper()
        if self.currency_repo.code_exists(store=store, code=code):
            raise ConflictError("This currency is already configured.", code="currency_exists")
        return Currency.objects.create(store=store, **{**data, "code": code})

    @atomic
    def create_exchange_rate(self, *, store, data: dict) -> ExchangeRate:
        base_code = data["base_code"].strip().upper()
        target_code = data["target_code"].strip().upper()
        if base_code == target_code:
            raise ConflictError("Base and target currencies must differ.", code="same_currency")
        existing = ExchangeRate.all_objects.filter(
            store=store, base_code=base_code, target_code=target_code, is_deleted=False
        ).first()
        if existing is not None:
            existing.rate = data["rate"]
            existing.save(update_fields=["rate", "updated_at"])
            return existing
        return ExchangeRate.objects.create(
            store=store, base_code=base_code, target_code=target_code, rate=data["rate"]
        )
