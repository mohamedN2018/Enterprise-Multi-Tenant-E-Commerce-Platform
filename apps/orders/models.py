"""Ordering domain models (store-scoped via ``TenantOwnedModel``).

* ``Cart`` / ``CartItem`` — a buyer's working basket within a store (one active
  cart per store+buyer); items snapshot the unit price at add-time.
* ``Order`` / ``OrderItem`` — the immutable result of checkout; items snapshot
  name/sku/price so historical orders are unaffected by later catalog edits.

Stock is reserved at checkout and committed/released as the order is
confirmed/cancelled (see ``CheckoutService``). This is a minimal order
lifecycle; payments, fulfilment, refunds and a richer timeline come later.
"""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.models import TenantOwnedModel


class CartStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    CHECKED_OUT = "checked_out", "Checked out"
    ABANDONED = "abandoned", "Abandoned"


class Cart(TenantOwnedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="carts"
    )
    status = models.CharField(
        max_length=16, choices=CartStatus.choices, default=CartStatus.ACTIVE, db_index=True
    )

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Cart"
        verbose_name_plural = "Carts"
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["store", "user"],
                condition=Q(status="active", is_deleted=False),
                name="uniq_active_cart_per_store_user",
            )
        ]

    def __str__(self) -> str:
        return f"Cart<{self.user_id}@{self.store_id}:{self.status}>"

    @property
    def subtotal(self) -> Decimal:
        return sum((item.line_total for item in self.items.all()), Decimal("0.00"))


class CartItem(TenantOwnedModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(
        "catalog.ProductVariant", on_delete=models.PROTECT, related_name="+"
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Cart item"
        verbose_name_plural = "Cart items"
        ordering = ("created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "variant"],
                condition=Q(is_deleted=False),
                name="uniq_cart_variant",
            )
        ]

    def __str__(self) -> str:
        return f"{self.quantity} x {self.variant_id}"

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity


class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    CONFIRMED = "confirmed", "Confirmed"
    CANCELLED = "cancelled", "Cancelled"


class Order(TenantOwnedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders"
    )
    number = models.CharField(max_length=40)
    status = models.CharField(
        max_length=16, choices=OrderStatus.choices, default=OrderStatus.PENDING, db_index=True
    )
    currency = models.CharField(max_length=3, default="USD")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    placed_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ("-placed_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["store", "number"],
                condition=Q(is_deleted=False),
                name="uniq_order_store_number",
            )
        ]
        indexes = [models.Index(fields=["store", "status"]), models.Index(fields=["user"])]

    def __str__(self) -> str:
        return self.number


class OrderItem(TenantOwnedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(
        "catalog.ProductVariant", on_delete=models.PROTECT, related_name="+"
    )
    product_name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Order item"
        verbose_name_plural = "Order items"
        ordering = ("created_at",)

    def __str__(self) -> str:
        return f"{self.quantity} x {self.sku}"
