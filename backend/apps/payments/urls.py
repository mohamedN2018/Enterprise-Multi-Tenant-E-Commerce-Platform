"""Payment API routes (mounted under /api/v1/payments/). Store via header."""

from django.urls import path

from apps.payments import views

app_name = "payments"

urlpatterns = [
    path("", views.PaymentListCreateView.as_view(), name="list"),
    path("gateways/", views.GatewayListView.as_view(), name="gateways"),
    path("<uuid:payment_id>/", views.PaymentDetailView.as_view(), name="detail"),
    path("<uuid:payment_id>/capture/", views.PaymentCaptureView.as_view(), name="capture"),
]
