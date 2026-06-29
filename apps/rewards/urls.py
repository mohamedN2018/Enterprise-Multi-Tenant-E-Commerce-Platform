"""Rewards API routes (mounted under /api/v1/rewards/). Store via header."""

from django.urls import path

from apps.rewards import views

app_name = "rewards"

urlpatterns = [
    # Buyer
    path("wallet/", views.WalletView.as_view(), name="wallet"),
    path("gift-cards/redeem/", views.GiftCardRedeemView.as_view(), name="gift-card-redeem"),
    path("loyalty/", views.LoyaltyView.as_view(), name="loyalty"),
    path("loyalty/redeem/", views.LoyaltyRedeemView.as_view(), name="loyalty-redeem"),
    # Staff
    path("gift-cards/", views.GiftCardListCreateView.as_view(), name="gift-card-list"),
]
