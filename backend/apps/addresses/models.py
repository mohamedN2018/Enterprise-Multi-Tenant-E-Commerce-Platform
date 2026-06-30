"""Address book (store-scoped via ``TenantOwnedModel``).

A buyer's saved shipping addresses within a store. At checkout the chosen address
is *snapshotted* onto the order (so later edits/deletes never alter history).
"""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import TenantOwnedModel


class Address(TenantOwnedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="addresses"
    )
    label = models.CharField(max_length=60, blank=True)  # "Home", "Work"
    full_name = models.CharField(max_length=150)
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120)
    region = models.CharField(max_length=120, blank=True)  # state / province
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=2)  # ISO 3166-1 alpha-2
    phone = models.CharField(max_length=40, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Address"
        verbose_name_plural = "Addresses"
        ordering = ("-is_default", "-created_at")
        indexes = [models.Index(fields=["store", "user"])]

    def __str__(self) -> str:
        return f"{self.full_name}, {self.city} ({self.country})"

    def snapshot(self) -> dict:
        return {
            "full_name": self.full_name,
            "line1": self.line1,
            "line2": self.line2,
            "city": self.city,
            "region": self.region,
            "postal_code": self.postal_code,
            "country": self.country,
            "phone": self.phone,
        }
