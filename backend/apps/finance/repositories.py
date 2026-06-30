"""Finance repositories (tenant-scoped)."""

from __future__ import annotations

from apps.core.repositories import BaseRepository
from apps.finance.models import Currency, ExchangeRate, TaxZone


class TaxZoneRepository(BaseRepository[TaxZone]):
    model = TaxZone

    def code_exists(self, *, store, code: str, exclude_pk=None) -> bool:
        qs = TaxZone.all_objects.filter(store=store, code=code, is_deleted=False)
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        return qs.exists()


class CurrencyRepository(BaseRepository[Currency]):
    model = Currency

    def code_exists(self, *, store, code: str) -> bool:
        return Currency.all_objects.filter(store=store, code=code, is_deleted=False).exists()


class ExchangeRateRepository(BaseRepository[ExchangeRate]):
    model = ExchangeRate
