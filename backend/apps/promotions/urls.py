"""Promotions API routes (mounted under /api/v1/promotions/). Store via header."""

from django.urls import path

from apps.promotions import views

app_name = "promotions"

urlpatterns = [
    path("coupons/", views.CouponListCreateView.as_view(), name="coupon-list"),
    path("coupons/<uuid:coupon_id>/", views.CouponDetailView.as_view(), name="coupon-detail"),
    # Automatic campaigns.
    path("campaigns/", views.CampaignListCreateView.as_view(), name="campaign-list"),
    path("campaigns/active/", views.ActiveCampaignListView.as_view(), name="campaign-active"),
    path(
        "campaigns/<uuid:campaign_id>/",
        views.CampaignDetailView.as_view(),
        name="campaign-detail",
    ),
    path(
        "campaigns/<uuid:campaign_id>/products/",
        views.CampaignProductListCreateView.as_view(),
        name="campaign-product-list",
    ),
    path(
        "campaigns/<uuid:campaign_id>/products/<uuid:link_id>/",
        views.CampaignProductDetailView.as_view(),
        name="campaign-product-detail",
    ),
]
