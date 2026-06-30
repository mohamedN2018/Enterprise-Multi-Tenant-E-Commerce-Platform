"""Procurement API routes (mounted under /api/v1/procurement/). Store via header."""

from django.urls import path

from apps.procurement import views

app_name = "procurement"

urlpatterns = [
    # Suppliers
    path("suppliers/", views.SupplierListCreateView.as_view(), name="supplier-list"),
    path(
        "suppliers/<uuid:supplier_id>/",
        views.SupplierDetailView.as_view(),
        name="supplier-detail",
    ),
    # Purchase orders
    path("purchase-orders/", views.PurchaseOrderListCreateView.as_view(), name="po-list"),
    path(
        "purchase-orders/<uuid:po_id>/",
        views.PurchaseOrderDetailView.as_view(),
        name="po-detail",
    ),
    path(
        "purchase-orders/<uuid:po_id>/submit/",
        views.PurchaseOrderSubmitView.as_view(),
        name="po-submit",
    ),
    path(
        "purchase-orders/<uuid:po_id>/receive/",
        views.PurchaseOrderReceiveView.as_view(),
        name="po-receive",
    ),
    path(
        "purchase-orders/<uuid:po_id>/cancel/",
        views.PurchaseOrderCancelView.as_view(),
        name="po-cancel",
    ),
    # Batches & serials
    path("batches/", views.StockBatchListView.as_view(), name="batch-list"),
    path("serials/", views.SerialNumberListCreateView.as_view(), name="serial-list"),
    path("serials/<uuid:serial_id>/", views.SerialNumberDetailView.as_view(), name="serial-detail"),
    # Manufacturing: bills of materials
    path("boms/", views.BillOfMaterialsListCreateView.as_view(), name="bom-list"),
    path("boms/<uuid:bom_id>/", views.BillOfMaterialsDetailView.as_view(), name="bom-detail"),
    path(
        "boms/<uuid:bom_id>/components/",
        views.BOMComponentListCreateView.as_view(),
        name="bom-component-list",
    ),
    # Manufacturing: work orders
    path("work-orders/", views.WorkOrderListCreateView.as_view(), name="work-order-list"),
    path(
        "work-orders/<uuid:work_order_id>/",
        views.WorkOrderDetailView.as_view(),
        name="work-order-detail",
    ),
    path(
        "work-orders/<uuid:work_order_id>/complete/",
        views.WorkOrderCompleteView.as_view(),
        name="work-order-complete",
    ),
    path(
        "work-orders/<uuid:work_order_id>/cancel/",
        views.WorkOrderCancelView.as_view(),
        name="work-order-cancel",
    ),
]
