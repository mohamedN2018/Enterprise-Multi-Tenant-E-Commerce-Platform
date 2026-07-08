"""Review application service: create + moderate reviews, votes, rating summary."""

from __future__ import annotations

from django.db.models import Avg, Count

from apps.core.exceptions import ConflictError, ValidationError
from apps.core.services import BaseService, atomic
from apps.reviews.models import Review, ReviewStatus, ReviewVote


def _validate_rating(rating: int) -> int:
    if rating is None or not (1 <= int(rating) <= 5):
        raise ValidationError("Rating must be between 1 and 5.", code="invalid_rating")
    return int(rating)


class ReviewService(BaseService):
    @atomic
    def create_review(self, *, store, user, product, rating, title="", body="") -> Review:
        rating = _validate_rating(rating)
        # A customer may only review a product they actually bought AND received.
        if not self._has_received(store=store, user=user, product=product):
            raise ValidationError(
                "You can only review a product after you have received it.",
                code="not_purchased",
            )
        if Review.all_objects.filter(
            store=store, product=product, user=user, is_deleted=False
        ).exists():
            raise ConflictError("You have already reviewed this product.", code="already_reviewed")
        return Review.objects.create(
            store=store,
            product=product,
            user=user,
            rating=rating,
            title=title,
            body=body,
            status=ReviewStatus.PENDING,
            is_verified_purchase=True,  # gated on a delivered order above
        )

    @atomic
    def update_review(self, *, review: Review, rating=None, title=None, body=None) -> Review:
        if rating is not None:
            review.rating = _validate_rating(rating)
        if title is not None:
            review.title = title
        if body is not None:
            review.body = body
        review.status = ReviewStatus.PENDING  # re-moderate after an edit
        review.save()
        return review

    def delete_review(self, *, review: Review) -> None:
        review.delete()

    @atomic
    def moderate(self, *, review: Review, approve: bool) -> Review:
        review.status = ReviewStatus.APPROVED if approve else ReviewStatus.REJECTED
        review.save(update_fields=["status", "updated_at"])
        return review

    @atomic
    def vote_helpful(self, *, store, review: Review, user, is_helpful: bool = True) -> Review:
        vote, _ = ReviewVote.objects.get_or_create(
            store=store, review=review, user=user, defaults={"is_helpful": is_helpful}
        )
        if vote.is_helpful != is_helpful:
            vote.is_helpful = is_helpful
            vote.save(update_fields=["is_helpful", "updated_at"])
        count = ReviewVote.objects.filter(review=review, is_helpful=True).count()
        Review.objects.filter(pk=review.pk).update(helpful_count=count)
        review.helpful_count = count
        return review

    # --- Reads ---
    def approved_for_product(self, *, store, product):
        return Review.objects.filter(store=store, product=product, status=ReviewStatus.APPROVED)

    def summary(self, *, store, product) -> dict:
        queryset = self.approved_for_product(store=store, product=product)
        totals = queryset.aggregate(average=Avg("rating"), count=Count("id"))
        by_star = {
            row["rating"]: row["count"]
            for row in queryset.values("rating").annotate(count=Count("id"))
        }
        return {
            "product": str(product.id),
            "average_rating": round(float(totals["average"] or 0), 2),
            "count": totals["count"],
            "distribution": {str(star): by_star.get(star, 0) for star in range(1, 6)},
        }

    @staticmethod
    def _has_received(*, store, user, product) -> bool:
        """True only when the user has a DELIVERED order containing this product."""
        from apps.orders.models import OrderItem, OrderStatus

        return OrderItem.all_objects.filter(
            store=store,
            is_deleted=False,
            order__user=user,
            order__status=OrderStatus.DELIVERED,
            variant__product=product,
        ).exists()
