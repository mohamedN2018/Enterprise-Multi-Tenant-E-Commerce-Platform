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
    path("referrals/", views.ReferralListView.as_view(), name="referral-list"),
    path("referrals/code/", views.ReferralCodeView.as_view(), name="referral-code"),
    path("referrals/apply/", views.ReferralApplyView.as_view(), name="referral-apply"),
    # Staff
    path("gift-cards/", views.GiftCardListCreateView.as_view(), name="gift-card-list"),
]
