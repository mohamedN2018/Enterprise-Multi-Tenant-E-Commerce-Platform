"""Admin registration for reviews."""

from __future__ import annotations

from django.contrib import admin

from apps.reviews.models import Review, ReviewVote


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "user",
        "store",
        "rating",
        "status",
        "is_verified_purchase",
        "helpful_count",
        "created_at",
    )
    list_filter = ("status", "rating", "is_verified_purchase")
    search_fields = ("title", "body", "product__name", "user__email", "store__name")
    readonly_fields = ("helpful_count", "is_verified_purchase")


@admin.register(ReviewVote)
class ReviewVoteAdmin(admin.ModelAdmin):
    list_display = ("review", "user", "is_helpful", "created_at")
    list_filter = ("is_helpful",)
    search_fields = ("review__product__name", "user__email")
