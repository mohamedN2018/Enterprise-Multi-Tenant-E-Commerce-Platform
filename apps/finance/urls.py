"""Finance API routes (mounted under /api/v1/finance/). Store via header."""

from django.urls import path

from apps.finance import views

app_name = "finance"

urlpatterns = [
    # Tax
    path("tax-zones/", views.TaxZoneListCreateView.as_view(), name="tax-zone-list"),
    path("tax-zones/<uuid:zone_id>/", views.TaxZoneDetailView.as_view(), name="tax-zone-detail"),
    path(
        "tax-zones/<uuid:zone_id>/rates/",
        views.TaxRateListCreateView.as_view(),
        name="tax-rate-list",
    ),
    # Currency
    path("currencies/", views.CurrencyListCreateView.as_view(), name="currency-list"),
    path("exchange-rates/", views.ExchangeRateListCreateView.as_view(), name="exchange-rate-list"),
    path("convert/", views.ConvertView.as_view(), name="convert"),
]
