"""Promotions domain models (store-scoped via ``TenantOwnedModel``).

* ``Coupon``            — a discount code with type, limits and a validity window.
* ``CouponRedemption``  — append-only record of each use (enforces per-user limits).
"""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.models import TenantOwnedModel


class DiscountType(models.TextChoices):
    PERCENTAGE = "percentage", "Percentage"
    FIXED = "fixed", "Fixed amount"


class Coupon(TenantOwnedModel):
    code = models.CharField(max_length=64)
    description = models.CharField(max_length=255, blank=True)
    discount_type = models.CharField(max_length=16, choices=DiscountType.choices)
    value = models.DecimalField(max_digits=12, decimal_places=2)

    # Optional constraints.
    min_spend = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    max_discount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    per_user_limit = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0, editable=False)

    # Validity window.
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["store", "code"],
                condition=Q(is_deleted=False),
                name="uniq_coupon_store_code",
            )
        ]

    def __str__(self) -> str:
        return self.code

    def is_within_window(self) -> bool:
        now = timezone.now()
        if self.starts_at and now < self.starts_at:
            return False
        return not (self.ends_at and now > self.ends_at)

    def has_global_capacity(self) -> bool:
        return self.usage_limit is None or self.used_count < self.usage_limit


class CouponRedemption(TenantOwnedModel):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name="redemptions")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="coupon_redemptions"
    )
    order = models.ForeignKey(
        "orders.Order", on_delete=models.CASCADE, related_name="coupon_redemptions"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Coupon redemption"
        verbose_name_plural = "Coupon redemptions"
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["coupon", "user"])]

    def __str__(self) -> str:
        return f"{self.coupon_id} by {self.user_id}: {self.amount}"
