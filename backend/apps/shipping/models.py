"""Shipping domain models (store-scoped).

* ``ShippingZone``   — a delivery region, matched EITHER by country (list) OR by a
  circle on the map (a centre point + a radius in km). A store can mix both: local
  circles for on-the-map delivery and country zones for wider shipping.
* ``ShippingMethod`` — a rate within a zone: base price + optional per-kg charge,
  with an optional free-shipping threshold on the order subtotal.

The chosen method's cost is added to the order total at checkout, and a geo zone
also gates *whether* delivery is offered at the buyer's pinned location.
"""

from __future__ import annotations

import math
from decimal import Decimal

from django.db import models
from django.db.models import Q

from apps.core.models import TenantOwnedModel

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1, lng1, lat2, lng2) -> float:
    """Great-circle distance in km between two lat/lng points."""
    rlat1, rlat2 = math.radians(float(lat1)), math.radians(float(lat2))
    dlat = rlat2 - rlat1
    dlng = math.radians(float(lng2) - float(lng1))
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlng / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))


class ShippingZone(TenantOwnedModel):
    name = models.CharField(max_length=120)
    code = models.SlugField(max_length=120)
    countries = models.JSONField(default=list, blank=True)
    is_default = models.BooleanField(default=False)
    # Map (geo) zone: a circle the store delivers within. When radius + centre are
    # set, this zone is matched by the buyer's location instead of by country.
    center_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    center_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    radius_km = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)

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

    @property
    def is_geo(self) -> bool:
        return (
            self.radius_km is not None
            and self.center_lat is not None
            and self.center_lng is not None
        )

    def covers(self, country: str | None) -> bool:
        return bool(country) and country in (self.countries or [])

    def covers_point(self, lat, lng) -> bool:
        """True when (lat, lng) falls inside this geo zone's circle."""
        if not self.is_geo or lat is None or lng is None:
            return False
        return haversine_km(self.center_lat, self.center_lng, lat, lng) <= float(self.radius_km)

    def distance_km(self, lat, lng):
        """Distance in km from the zone centre to a point (None if not a geo zone)."""
        if not self.is_geo or lat is None or lng is None:
            return None
        return haversine_km(self.center_lat, self.center_lng, lat, lng)


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
