"""Inventory API routes (mounted under /api/v1/inventory/). Store via header."""

from django.urls import path

from apps.inventory import views

app_name = "inventory"

urlpatterns = [
    # Warehouses
    path("warehouses/", views.WarehouseListCreateView.as_view(), name="warehouse-list"),
    path(
        "warehouses/<uuid:warehouse_id>/",
        views.WarehouseDetailView.as_view(),
        name="warehouse-detail",
    ),
    # Stock
    path("stock/", views.StockItemListView.as_view(), name="stock-list"),
    path("stock/low/", views.LowStockListView.as_view(), name="stock-low"),
    path("stock/receive/", views.ReceiveStockView.as_view(), name="stock-receive"),
    path("stock/adjust/", views.AdjustStockView.as_view(), name="stock-adjust"),
    path("stock/transfer/", views.TransferStockView.as_view(), name="stock-transfer"),
    # Ledger
    path("movements/", views.StockMovementListView.as_view(), name="movement-list"),
]
