"""Order API routes (mounted under /api/v1/orders/). Store via header."""

from django.urls import path

from apps.orders import views

app_name = "orders"

urlpatterns = [
    # Staff (store-scoped) — must precede the buyer <uuid> routes.
    path("manage/", views.OrderManageListView.as_view(), name="manage"),
    path("manage/<uuid:order_id>/", views.OrderManageDetailView.as_view(), name="manage-detail"),
    path(
        "manage/<uuid:order_id>/confirm/",
        views.OrderManageConfirmView.as_view(),
        name="manage-confirm",
    ),
    path(
        "manage/<uuid:order_id>/cancel/",
        views.OrderManageCancelView.as_view(),
        name="manage-cancel",
    ),
    path(
        "manage/<uuid:order_id>/status/",
        views.OrderManageStatusView.as_view(),
        name="manage-status",
    ),
    path(
        "manage/<uuid:order_id>/push-to-cashier/",
        views.OrderManagePushView.as_view(),
        name="manage-push",
    ),
    # Buyer
    path("", views.OrderListView.as_view(), name="list"),
    path("<uuid:order_id>/", views.OrderDetailView.as_view(), name="detail"),
    path("<uuid:order_id>/confirm/", views.OrderConfirmView.as_view(), name="confirm"),
    path("<uuid:order_id>/cancel/", views.OrderCancelView.as_view(), name="cancel"),
]
