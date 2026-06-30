"""Review domain models (store-scoped via ``TenantOwnedModel``).

* ``Review``     — a buyer's star rating + comment on a product, moderated
  (pending -> approved / rejected) before it shows publicly. Flagged as a
  verified purchase when the reviewer has a confirmed order for the product.
* ``ReviewVote`` — a "was this helpful?" vote, one per user per review.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.models import TenantOwnedModel


class ReviewStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class Review(TenantOwnedModel):
    product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField()  # 1..5 (enforced in the service)
    title = models.CharField(max_length=150, blank=True)
    body = models.TextField(blank=True)
    status = models.CharField(
        max_length=10, choices=ReviewStatus.choices, default=ReviewStatus.PENDING, db_index=True
    )
    is_verified_purchase = models.BooleanField(default=False)
    helpful_count = models.PositiveIntegerField(default=0, editable=False)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["store", "product", "user"],
                condition=Q(is_deleted=False),
                name="uniq_review_store_product_user",
            )
        ]
        indexes = [models.Index(fields=["product", "status"])]

    def __str__(self) -> str:
        return f"{self.rating}* {self.product_id} by {self.user_id}"


class ReviewVote(TenantOwnedModel):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    is_helpful = models.BooleanField(default=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Review vote"
        verbose_name_plural = "Review votes"
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["review", "user"],
                condition=Q(is_deleted=False),
                name="uniq_review_vote_user",
            )
        ]

    def __str__(self) -> str:
        return f"{self.review_id}:{self.user_id}={self.is_helpful}"
