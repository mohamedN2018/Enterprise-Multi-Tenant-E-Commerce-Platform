"""Finance domain models (store-scoped): tax engine + multi-currency.

* ``TaxZone`` / ``TaxRate`` — geographic tax zones (matched by country) with one
  or more rates (e.g. VAT). The combined active rate is applied at checkout.
* ``Currency`` / ``ExchangeRate`` — enabled currencies and conversion rates for
  display / multi-currency quoting.
"""

from __future__ import annotations

from django.db import models
from django.db.models import Q

from apps.core.models import TenantOwnedModel


class TaxZone(TenantOwnedModel):
    name = models.CharField(max_length=120)
    code = models.SlugField(max_length=120)
    # ISO country codes this zone covers; empty + is_default => catch-all.
    countries = models.JSONField(default=list, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Tax zone"
        verbose_name_plural = "Tax zones"
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["store", "code"],
                condition=Q(is_deleted=False),
                name="uniq_tax_zone_store_code",
            )
        ]

    def __str__(self) -> str:
        return self.name

    def covers(self, country: str | None) -> bool:
        return bool(country) and country in (self.countries or [])


class TaxRate(TenantOwnedModel):
    zone = models.ForeignKey(TaxZone, on_delete=models.CASCADE, related_name="rates")
    name = models.CharField(max_length=120)
    rate = models.DecimalField(max_digits=6, decimal_places=3)  # percentage
    priority = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Tax rate"
        verbose_name_plural = "Tax rates"
        ordering = ("priority", "name")
        indexes = [models.Index(fields=["zone", "is_active"])]

    def __str__(self) -> str:
        return f"{self.name} {self.rate}%"


class Currency(TenantOwnedModel):
    code = models.CharField(max_length=3)  # ISO 4217
    name = models.CharField(max_length=80, blank=True)
    symbol = models.CharField(max_length=8, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Currency"
        verbose_name_plural = "Currencies"
        ordering = ("code",)
        constraints = [
            models.UniqueConstraint(
                fields=["store", "code"],
                condition=Q(is_deleted=False),
                name="uniq_currency_store_code",
            )
        ]

    def __str__(self) -> str:
        return self.code


class ExchangeRate(TenantOwnedModel):
    base_code = models.CharField(max_length=3)
    target_code = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=18, decimal_places=8)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Exchange rate"
        verbose_name_plural = "Exchange rates"
        ordering = ("base_code", "target_code")
        constraints = [
            models.UniqueConstraint(
                fields=["store", "base_code", "target_code"],
                condition=Q(is_deleted=False),
                name="uniq_exchange_rate",
            )
        ]

    def __str__(self) -> str:
        return f"{self.base_code}->{self.target_code} @ {self.rate}"
