"""Reviews API: buyer create/list/edit/vote, public approved feed, staff moderation."""

from __future__ import annotations

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.catalog.models import Product
from apps.core.exceptions import NotFoundError
from apps.core.mixins import BaseAPIView, BaseGenericAPIView
from apps.core.responses import APIResponse
from apps.reviews.models import Review, ReviewStatus
from apps.reviews.serializers import (
    CreateReviewSerializer,
    ReviewSerializer,
    UpdateReviewSerializer,
    VoteSerializer,
)
from apps.reviews.services import ReviewService
from apps.stores.context import RequireStoreMixin, StoreContextMixin


def _validated(serializer_class, request) -> dict:
    serializer = serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def _product(product_id) -> Product:
    product = Product.objects.filter(id=product_id).first()
    if product is None:
        raise NotFoundError("Product not found.")
    return product


# --- Buyer / public --------------------------------------------------------
class ReviewListCreateView(RequireStoreMixin, BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewSerializer

    def get_queryset(self):
        queryset = Review.objects.filter(store=self.store, status=ReviewStatus.APPROVED)
        product_id = self.request.query_params.get("product")
        return queryset.filter(product_id=product_id) if product_id else queryset

    def post(self, request: Request, *args, **kwargs) -> Response:
        data = _validated(CreateReviewSerializer, request)
        review = ReviewService().create_review(
            store=self.store,
            user=request.user,
            product=_product(data["product_id"]),
            rating=data["rating"],
            title=data["title"],
            body=data["body"],
        )
        return APIResponse.success(
            ReviewSerializer(review).data,
            message="Review submitted for moderation.",
            status_code=201,
        )


class ReviewMineView(RequireStoreMixin, BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(store=self.store, user=self.request.user)


class ReviewSummaryView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        product = _product(request.query_params.get("product"))
        return APIResponse.success(ReviewService().summary(store=self.store, product=product))


class ReviewDetailView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def _own_review(self, request, review_id) -> Review:
        review = Review.objects.filter(id=review_id, user=request.user).first()
        if review is None:
            raise NotFoundError("Review not found.")
        return review

    def get(self, request: Request, review_id) -> Response:
        return APIResponse.success(ReviewSerializer(self._own_review(request, review_id)).data)

    def patch(self, request: Request, review_id) -> Response:
        data = _validated(UpdateReviewSerializer, request)
        review = ReviewService().update_review(
            review=self._own_review(request, review_id),
            rating=data.get("rating"),
            title=data.get("title"),
            body=data.get("body"),
        )
        return APIResponse.success(ReviewSerializer(review).data, message="Review updated.")

    def delete(self, request: Request, review_id) -> Response:
        ReviewService().delete_review(review=self._own_review(request, review_id))
        return APIResponse.success(message="Review removed.")


class ReviewVoteView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, review_id) -> Response:
        review = Review.objects.filter(id=review_id, status=ReviewStatus.APPROVED).first()
        if review is None:
            raise NotFoundError("Review not found.")
        data = _validated(VoteSerializer, request)
        review = ReviewService().vote_helpful(
            store=self.store, review=review, user=request.user, is_helpful=data["is_helpful"]
        )
        return APIResponse.success(
            ReviewSerializer(review).data, message="Thanks for your feedback."
        )


# --- Staff moderation ------------------------------------------------------
class ReviewModerationListView(StoreContextMixin, BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewSerializer
    filterset_fields = ("status", "product")

    def get_queryset(self):
        return Review.objects.all()


class _ModerateView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]
    approve = True
    message = ""

    def post(self, request: Request, review_id) -> Response:
        self.require_write()
        review = Review.objects.filter(id=review_id).first()
        if review is None:
            raise NotFoundError("Review not found.")
        review = ReviewService().moderate(review=review, approve=self.approve)
        return APIResponse.success(ReviewSerializer(review).data, message=self.message)


class ReviewApproveView(_ModerateView):
    approve = True
    message = "Review approved."


class ReviewRejectView(_ModerateView):
    approve = False
    message = "Review rejected."
