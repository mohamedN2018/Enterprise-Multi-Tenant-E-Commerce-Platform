"""Search API routes (mounted under /api/v1/search/). Store via header."""

from django.urls import path

from apps.search import views

app_name = "search"

urlpatterns = [
    path("products/", views.ProductSearchView.as_view(), name="product-search"),
]
