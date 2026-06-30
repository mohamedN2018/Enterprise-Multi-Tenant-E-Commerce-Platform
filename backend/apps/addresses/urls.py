"""Address API routes (mounted under /api/v1/addresses/). Store via header."""

from django.urls import path

from apps.addresses import views

app_name = "addresses"

urlpatterns = [
    path("", views.AddressListCreateView.as_view(), name="list"),
    path("<uuid:address_id>/", views.AddressDetailView.as_view(), name="detail"),
    path("<uuid:address_id>/default/", views.AddressSetDefaultView.as_view(), name="set-default"),
]
