"""Stores API routes (mounted under /api/v1/stores/)."""

from django.urls import path

from apps.stores import views

app_name = "stores"

urlpatterns = [
    path("", views.StoreListCreateView.as_view(), name="store-list"),
    path("<uuid:store_id>/", views.StoreDetailView.as_view(), name="store-detail"),
    path("<uuid:store_id>/settings/", views.StoreSettingsView.as_view(), name="store-settings"),
    path("<uuid:store_id>/members/", views.MemberListCreateView.as_view(), name="member-list"),
    path(
        "<uuid:store_id>/members/<uuid:member_id>/",
        views.MemberDetailView.as_view(),
        name="member-detail",
    ),
    path(
        "<uuid:store_id>/limit-requests/",
        views.StoreLimitRequestView.as_view(),
        name="limit-requests",
    ),
]
