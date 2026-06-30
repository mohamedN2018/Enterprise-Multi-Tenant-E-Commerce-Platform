"""Shipping domain models (store-scoped).

* ``ShippingZone``   — a destination region (matched by country).
* ``ShippingMethod`` — a rate within a zone: base price + optional per-kg charge,
  with an optional free-shipping threshold on the order subtotal.

The chosen method's cost is added to the order total at checkout.
"""

from __future__ import annotations

from decimal import Decimal

from django.db import models
from django.db.models import Q

from apps.core.models import TenantOwnedModel


class ShippingZone(TenantOwnedModel):
    name = models.CharField(max_length=120)
    code = models.SlugField(max_length=120)
    countries = models.JSONField(default=list, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Shipping zone"
        verbose_name_plural = "Shipping zones"
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["store", "code"],
                condition=Q(is_deleted=False),
                name="uniq_shipping_zone_store_code",
            )
        ]

    def __str__(self) -> str:
        return self.name

    def covers(self, country: str | None) -> bool:
        return bool(country) and country in (self.countries or [])


class ShippingMethod(TenantOwnedModel):
    zone = models.ForeignKey(ShippingZone, on_delete=models.CASCADE, related_name="methods")
    name = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    per_kg = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    # Free shipping when the order subtotal reaches this threshold.
    free_over = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Shipping method"
        verbose_name_plural = "Shipping methods"
        ordering = ("price", "name")
        indexes = [models.Index(fields=["zone", "is_active"])]

    def __str__(self) -> str:
        return self.name

    def quote(self, *, subtotal: Decimal, weight: Decimal) -> Decimal:
        if self.free_over is not None and subtotal >= self.free_over:
            return Decimal("0.00")
        return self.price + (self.per_kg * Decimal(weight))
