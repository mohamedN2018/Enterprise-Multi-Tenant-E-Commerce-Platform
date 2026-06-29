"""Returns (RMA) domain models (store-scoped).

* ``ReturnRequest`` — a buyer's request to return items from a confirmed order,
  moving through requested -> approved -> refunded (or rejected/cancelled).
* ``ReturnItem``    — the specific order line + quantity being returned.

On refund the order's items are restocked into inventory and the buyer is repaid:
to the original payment gateway when one captured the order (via
``PaymentGateway.refund``), otherwise — or when ``STORE_CREDIT`` was chosen — to
their wallet as store credit.
"""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.core.models import TenantOwnedModel


class ReturnStatus(models.TextChoices):
    REQUESTED = "requested", "Requested"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    REFUNDED = "refunded", "Refunded"
    CANCELLED = "cancelled", "Cancelled"


class ReturnResolution(models.TextChoices):
    REFUND = "refund", "Refund"
    EXCHANGE = "exchange", "Exchange"
    STORE_CREDIT = "store_credit", "Store credit"


#: Statuses that still hold a claim on the returned quantity.
ACTIVE_RETURN_STATUSES = (
    ReturnStatus.REQUESTED,
    ReturnStatus.APPROVED,
    ReturnStatus.REFUNDED,
)


class ReturnRequest(TenantOwnedModel):
    order = models.ForeignKey("orders.Order", on_delete=models.PROTECT, related_name="returns")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="returns"
    )
    status = models.CharField(
        max_length=16, choices=ReturnStatus.choices, default=ReturnStatus.REQUESTED, db_index=True
    )
    resolution = models.CharField(
        max_length=16, choices=ReturnResolution.choices, default=ReturnResolution.REFUND
    )
    reason = models.TextField(blank=True)
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    refund_reference = models.CharField(max_length=255, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Return request"
        verbose_name_plural = "Return requests"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["store", "status"]),
            models.Index(fields=["user"]),
            models.Index(fields=["order"]),
        ]

    def __str__(self) -> str:
        return f"RMA {self.id} ({self.status})"


class ReturnItem(TenantOwnedModel):
    return_request = models.ForeignKey(
        ReturnRequest, on_delete=models.CASCADE, related_name="items"
    )
    order_item = models.ForeignKey("orders.OrderItem", on_delete=models.PROTECT, related_name="+")
    variant = models.ForeignKey(
        "catalog.ProductVariant", on_delete=models.PROTECT, related_name="+"
    )
    quantity = models.PositiveIntegerField()
    reason = models.CharField(max_length=255, blank=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Return item"
        verbose_name_plural = "Return items"
        ordering = ("created_at",)

    def __str__(self) -> str:
        return f"{self.quantity} x {self.variant_id}"
