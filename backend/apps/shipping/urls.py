"""Shipping API routes (mounted under /api/v1/shipping/). Store via header."""

from django.urls import path

from apps.shipping import views

app_name = "shipping"

urlpatterns = [
    # Zones & methods (staff)
    path("zones/", views.ShippingZoneListCreateView.as_view(), name="zone-list"),
    path("zones/<uuid:zone_id>/", views.ShippingZoneDetailView.as_view(), name="zone-detail"),
    path(
        "zones/<uuid:zone_id>/methods/",
        views.ShippingMethodListCreateView.as_view(),
        name="method-list",
    ),
    # Tracking (staff)
    path(
        "orders/<uuid:order_id>/tracking/",
        views.OrderTrackingView.as_view(),
        name="order-tracking",
    ),
    # Available methods (buyer)
    path("methods/", views.AvailableMethodsView.as_view(), name="available-methods"),
]
