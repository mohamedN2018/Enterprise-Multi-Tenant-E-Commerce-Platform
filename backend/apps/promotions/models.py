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


class CampaignType(models.TextChoices):
    FLASH_SALE = "flash_sale", "Flash sale"
    BUY_X_GET_Y = "buy_x_get_y", "Buy X get Y"
    ORDER_DISCOUNT = "order_discount", "Order discount"
    FREE_SHIPPING = "free_shipping", "Free shipping"


class Campaign(TenantOwnedModel):
    """An automatic, code-less promotion evaluated at checkout.

    Unlike a ``Coupon`` (entered manually), a campaign applies on its own while it
    is *live* (active + within its window) and its conditions are met. The kind of
    benefit is driven by ``campaign_type``; the relevant config fields are:

    * ``FLASH_SALE``     — ``discount_type``/``discount_value`` off matching lines
      (the ``products`` set); ``max_discount`` caps it.
    * ``BUY_X_GET_Y``    — for each ``buy_quantity + get_quantity`` matching units,
      ``get_quantity`` of the cheapest are discounted by ``get_discount_percent``
      (100 = free).
    * ``ORDER_DISCOUNT`` — ``discount_type``/``discount_value`` off the whole order
      once the subtotal reaches ``min_spend``.
    * ``FREE_SHIPPING``  — zeroes the shipping charge once the subtotal reaches
      ``min_spend``.

    Campaigns are applied highest ``priority`` first. A non-``stackable`` campaign
    is exclusive: it only applies if no other discount has yet, and once applied it
    blocks further discount campaigns (free shipping is evaluated independently).
    """

    name = models.CharField(max_length=150)
    description = models.CharField(max_length=255, blank=True)
    campaign_type = models.CharField(max_length=20, choices=CampaignType.choices)

    # Discount config (FLASH_SALE, ORDER_DISCOUNT).
    discount_type = models.CharField(max_length=16, choices=DiscountType.choices, blank=True)
    discount_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    max_discount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # Threshold (ORDER_DISCOUNT, FREE_SHIPPING).
    min_spend = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # Buy X get Y config.
    buy_quantity = models.PositiveIntegerField(null=True, blank=True)
    get_quantity = models.PositiveIntegerField(null=True, blank=True)
    get_discount_percent = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    # Engine controls.
    priority = models.IntegerField(default=0, db_index=True)
    stackable = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Campaign"
        verbose_name_plural = "Campaigns"
        ordering = ("-priority", "-created_at")
        indexes = [models.Index(fields=["store", "campaign_type", "is_active"])]

    def __str__(self) -> str:
        return self.name

    def is_live(self) -> bool:
        if not self.is_active:
            return False
        now = timezone.now()
        if self.starts_at and now < self.starts_at:
            return False
        return not (self.ends_at and now > self.ends_at)


class CampaignProduct(TenantOwnedModel):
    """A product targeted by a product-scoped campaign (flash sale / buy-X-get-Y)."""

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="products")
    product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="+")

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Campaign product"
        verbose_name_plural = "Campaign products"
        ordering = ("created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["campaign", "product"],
                condition=Q(is_deleted=False),
                name="uniq_campaign_product",
            )
        ]

    def __str__(self) -> str:
        return f"{self.campaign_id}:{self.product_id}"
