"""Fraud API routes (mounted under /api/v1/fraud/). Store via header. Staff only."""

from django.urls import path

from apps.fraud import views

app_name = "fraud"

urlpatterns = [
    path("checks/", views.FraudCheckListView.as_view(), name="check-list"),
    path("checks/<uuid:check_id>/", views.FraudCheckDetailView.as_view(), name="check-detail"),
    path("checks/<uuid:check_id>/clear/", views.FraudCheckClearView.as_view(), name="check-clear"),
    path(
        "checks/<uuid:check_id>/reject/",
        views.FraudCheckRejectView.as_view(),
        name="check-reject",
    ),
]
