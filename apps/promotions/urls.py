"""Promotions API routes (mounted under /api/v1/promotions/). Store via header."""

from django.urls import path

from apps.promotions import views

app_name = "promotions"

urlpatterns = [
    path("coupons/", views.CouponListCreateView.as_view(), name="coupon-list"),
    path("coupons/<uuid:coupon_id>/", views.CouponDetailView.as_view(), name="coupon-detail"),
]
