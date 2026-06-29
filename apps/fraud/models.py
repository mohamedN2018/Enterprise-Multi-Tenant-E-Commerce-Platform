"""Fraud domain model (store-scoped via ``TenantOwnedModel``).

``FraudCheck`` is the risk assessment attached to an order at checkout: an
automated ``decision`` (approve / review / reject) from the rule engine, plus a
manual ``resolution`` once a reviewer acts. While an order's check is in review
or reject with a pending resolution, confirmation is blocked.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import TenantOwnedModel


class FraudDecision(models.TextChoices):
    APPROVE = "approve", "Approve"
    REVIEW = "review", "Review"
    REJECT = "reject", "Reject"


class FraudResolution(models.TextChoices):
    PENDING = "pending", "Pending"
    CLEARED = "cleared", "Cleared"
    REJECTED = "rejected", "Rejected"


class FraudCheck(TenantOwnedModel):
    order = models.OneToOneField(
        "orders.Order", on_delete=models.CASCADE, related_name="fraud_check"
    )
    score = models.PositiveIntegerField(default=0)
    decision = models.CharField(
        max_length=10, choices=FraudDecision.choices, default=FraudDecision.APPROVE, db_index=True
    )
    resolution = models.CharField(
        max_length=10,
        choices=FraudResolution.choices,
        default=FraudResolution.PENDING,
        db_index=True,
    )
    reasons = models.JSONField(default=list, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Fraud check"
        verbose_name_plural = "Fraud checks"
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["store", "decision", "resolution"])]

    def __str__(self) -> str:
        return f"{self.order_id}: {self.decision}/{self.resolution} ({self.score})"

    @property
    def is_blocking(self) -> bool:
        return self.decision != FraudDecision.APPROVE and self.resolution == FraudResolution.PENDING
