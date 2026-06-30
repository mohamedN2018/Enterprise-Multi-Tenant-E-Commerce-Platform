"""Reviews API routes (mounted under /api/v1/reviews/). Store via header."""

from django.urls import path

from apps.reviews import views

app_name = "reviews"

urlpatterns = [
    path("", views.ReviewListCreateView.as_view(), name="list"),
    path("mine/", views.ReviewMineView.as_view(), name="mine"),
    path("summary/", views.ReviewSummaryView.as_view(), name="summary"),
    path("moderation/", views.ReviewModerationListView.as_view(), name="moderation"),
    path("<uuid:review_id>/", views.ReviewDetailView.as_view(), name="detail"),
    path("<uuid:review_id>/vote/", views.ReviewVoteView.as_view(), name="vote"),
    path("<uuid:review_id>/approve/", views.ReviewApproveView.as_view(), name="approve"),
    path("<uuid:review_id>/reject/", views.ReviewRejectView.as_view(), name="reject"),
]
