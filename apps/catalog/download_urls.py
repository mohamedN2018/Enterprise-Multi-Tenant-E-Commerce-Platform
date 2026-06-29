"""Buyer download routes (mounted under /api/v1/downloads/). Store via header."""

from django.urls import path

from apps.catalog import views

app_name = "downloads"

urlpatterns = [
    path("", views.DownloadGrantListView.as_view(), name="list"),
    path("<str:token>/", views.DownloadView.as_view(), name="download"),
]
