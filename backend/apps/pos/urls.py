"""Cashier (POS) routes (mounted under /api/v1/pos/).

* ``connection*`` — management, store via the X-Store-Id header (staff auth).
* ``sales`` / ``stock`` — machine endpoints, store via the API key.
"""

from django.urls import path

from apps.pos import views

app_name = "pos"

urlpatterns = [
    # Inbound: our key that a cashier uses to push sales / read stock.
    path("connection/", views.PosConnectionView.as_view(), name="connection"),
    path("connection/rotate/", views.PosConnectionRotateView.as_view(), name="connection-rotate"),
    path("sales/", views.PosSaleView.as_view(), name="sales"),
    path("stock/", views.PosStockView.as_view(), name="stock"),
    path("order-status/", views.PosOrderStatusView.as_view(), name="order-status"),
    # Outbound: link an external POS supplier and import its catalog.
    path("supplier/", views.PosSupplierView.as_view(), name="supplier"),
    path("supplier/import/", views.PosSupplierImportView.as_view(), name="supplier-import"),
]
