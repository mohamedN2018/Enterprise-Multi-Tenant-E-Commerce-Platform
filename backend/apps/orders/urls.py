"""Order API routes (mounted under /api/v1/orders/). Store via header."""

from django.urls import path

from apps.orders import views

app_name = "orders"

urlpatterns = [
    path("", views.OrderListView.as_view(), name="list"),
    path("<uuid:order_id>/", views.OrderDetailView.as_view(), name="detail"),
    path("<uuid:order_id>/confirm/", views.OrderConfirmView.as_view(), name="confirm"),
    path("<uuid:order_id>/cancel/", views.OrderCancelView.as_view(), name="cancel"),
]
