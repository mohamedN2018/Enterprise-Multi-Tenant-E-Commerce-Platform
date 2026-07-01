"""Payment API routes (mounted under /api/v1/payments/). Store via header."""

from django.urls import path

from apps.payments import views

app_name = "payments"

urlpatterns = [
    # Staff (store-scoped) — must precede the buyer <uuid> routes.
    path("manage/", views.PaymentManageListView.as_view(), name="manage"),
    path(
        "manage/<uuid:payment_id>/",
        views.PaymentManageDetailView.as_view(),
        name="manage-detail",
    ),
    path(
        "manage/<uuid:payment_id>/capture/",
        views.PaymentManageCaptureView.as_view(),
        name="manage-capture",
    ),
    # Buyer
    path("", views.PaymentListCreateView.as_view(), name="list"),
    path("gateways/", views.GatewayListView.as_view(), name="gateways"),
    path("<uuid:payment_id>/", views.PaymentDetailView.as_view(), name="detail"),
    path("<uuid:payment_id>/capture/", views.PaymentCaptureView.as_view(), name="capture"),
]
