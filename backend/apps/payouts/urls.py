"""Payouts API routes (mounted under /api/v1/payouts/). Store via header."""

from django.urls import path

from apps.payouts import views

app_name = "payouts"

urlpatterns = [
    path("account/", views.SellerAccountView.as_view(), name="account"),
    path("commission/", views.CommissionView.as_view(), name="commission"),
    path("ledger/", views.LedgerListView.as_view(), name="ledger"),
    path("", views.PayoutListCreateView.as_view(), name="list"),
    path("<uuid:payout_id>/mark-paid/", views.PayoutMarkPaidView.as_view(), name="mark-paid"),
]
