"""Platform (super-admin) routes, mounted under /api/v1/platform/."""

from django.urls import path

from apps.stores import platform_views as views

app_name = "platform"

urlpatterns = [
    path("stores/", views.PlatformStoreListCreateView.as_view(), name="store-list"),
    path("stores/<uuid:store_id>/", views.PlatformStoreDetailView.as_view(), name="store-detail"),
    path("sellers/", views.PlatformSellerListView.as_view(), name="seller-list"),
    path("sellers/<uuid:user_id>/", views.PlatformSellerDetailView.as_view(), name="seller-detail"),
    path("requests/", views.PlatformRequestListView.as_view(), name="request-list"),
    path(
        "requests/<uuid:request_id>/approve/",
        views.PlatformRequestApproveView.as_view(),
        name="request-approve",
    ),
    path(
        "requests/<uuid:request_id>/reject/",
        views.PlatformRequestRejectView.as_view(),
        name="request-reject",
    ),
]
