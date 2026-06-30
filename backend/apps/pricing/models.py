"""Pricing domain models (store-scoped via ``TenantOwnedModel``).

* ``CustomerGroup``            — a pricing audience (retail, wholesale, B2B, VIP).
* ``CustomerGroupMembership``  — assigns a buyer to one group per store.
* ``PriceRule``                — a variant price for an (optional) group, with a
  minimum-quantity break (tier pricing) and a fixed or percentage value.

The effective price for a (variant, buyer, quantity) is resolved by
``apps.pricing.services.PricingService`` and snapshotted onto the cart line.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.models import TenantOwnedModel


class CustomerGroup(TenantOwnedModel):
    name = models.CharField(max_length=120)
    code = models.SlugField(max_length=120)
    description = models.CharField(max_length=255, blank=True)
    is_default = models.BooleanField(default=False)
    priority = models.PositiveIntegerField(default=0)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Customer group"
        verbose_name_plural = "Customer groups"
        ordering = ("-priority", "name")
        constraints = [
            models.UniqueConstraint(
                fields=["store", "code"],
                condition=Q(is_deleted=False),
                name="uniq_customer_group_store_code",
            )
        ]

    def __str__(self) -> str:
        return self.name


class CustomerGroupMembership(TenantOwnedModel):
    customer_group = models.ForeignKey(
        CustomerGroup, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pricing_groups"
    )

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Customer group membership"
        verbose_name_plural = "Customer group memberships"
        constraints = [
            models.UniqueConstraint(
                fields=["store", "user"],
                condition=Q(is_deleted=False),
                name="uniq_pricing_group_per_store_user",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user_id} -> {self.customer_group_id}"


class PriceRuleType(models.TextChoices):
    FIXED = "fixed", "Fixed price"
    PERCENT_DISCOUNT = "percent_discount", "Percentage discount"


class PriceRule(TenantOwnedModel):
    variant = models.ForeignKey(
        "catalog.ProductVariant", on_delete=models.CASCADE, related_name="price_rules"
    )
    # null = applies to every buyer (regardless of group).
    customer_group = models.ForeignKey(
        CustomerGroup,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="price_rules",
    )
    min_quantity = models.PositiveIntegerField(default=1)
    rule_type = models.CharField(
        max_length=20, choices=PriceRuleType.choices, default=PriceRuleType.FIXED
    )
    value = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Price rule"
        verbose_name_plural = "Price rules"
        ordering = ("-min_quantity",)
        indexes = [
            models.Index(fields=["variant", "is_active"]),
            models.Index(fields=["customer_group"]),
        ]

    def __str__(self) -> str:
        return f"{self.variant_id} {self.rule_type}={self.value} (q>={self.min_quantity})"
