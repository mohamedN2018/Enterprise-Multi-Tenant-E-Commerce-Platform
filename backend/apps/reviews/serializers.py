"""Review serializers."""

from __future__ import annotations

from rest_framework import serializers

from apps.reviews.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = (
            "id",
            "product",
            "user",
            "rating",
            "title",
            "body",
            "status",
            "is_verified_purchase",
            "helpful_count",
            "created_at",
        )
        read_only_fields = fields


class CreateReviewSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    title = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    body = serializers.CharField(required=False, allow_blank=True, default="")


class UpdateReviewSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5, required=False)
    title = serializers.CharField(max_length=150, required=False, allow_blank=True)
    body = serializers.CharField(required=False, allow_blank=True)


class VoteSerializer(serializers.Serializer):
    is_helpful = serializers.BooleanField(required=False, default=True)
