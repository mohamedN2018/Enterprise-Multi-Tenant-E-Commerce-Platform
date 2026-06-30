"""Payment domain models (store-scoped via ``TenantOwnedModel``).

* ``Payment``       — a payment attempt against an order via a gateway.
* ``PaymentEvent``  — append-only log of gateway interactions for audit.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import TenantOwnedModel


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    CAPTURED = "captured", "Captured"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"
    REFUNDED = "refunded", "Refunded"


class Payment(TenantOwnedModel):
    order = models.ForeignKey("orders.Order", on_delete=models.PROTECT, related_name="payments")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="payments"
    )
    gateway = models.CharField(max_length=32, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(
        max_length=16,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
    )
    transaction_id = models.CharField(max_length=255, blank=True)
    redirect_url = models.URLField(blank=True)
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["store", "status"]),
            models.Index(fields=["order"]),
        ]

    def __str__(self) -> str:
        return f"{self.gateway} {self.amount} {self.currency} [{self.status}]"

    @property
    def is_captured(self) -> bool:
        return self.status == PaymentStatus.CAPTURED


class PaymentEvent(TenantOwnedModel):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=32)
    message = models.CharField(max_length=255, blank=True)
    data = models.JSONField(default=dict, blank=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Payment event"
        verbose_name_plural = "Payment events"
        ordering = ("created_at",)

    def __str__(self) -> str:
        return f"{self.event_type} ({self.payment_id})"
