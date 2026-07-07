"""Cashier (POS) routes (mounted under /api/v1/pos/).

* ``connection*`` — management, store via the X-Store-Id header (staff auth).
* ``sales`` / ``stock`` — machine endpoints, store via the API key.
"""

from django.urls import path

from apps.pos import views

app_name = "pos"

urlpatterns = [
    # Management (seller console)
    path("connection/", views.PosConnectionView.as_view(), name="connection"),
    path("connection/rotate/", views.PosConnectionRotateView.as_view(), name="connection-rotate"),
    # Cashier (API-key auth)
    path("sales/", views.PosSaleView.as_view(), name="sales"),
    path("stock/", views.PosStockView.as_view(), name="stock"),
]
