"""Catalog API routes (mounted under /api/v1/catalog/).

The active store is taken from the request context (X-Store-Id / X-Store-Slug
header), not the URL — every resource here is implicitly store-scoped.
"""

from django.urls import path

from apps.catalog import views

app_name = "catalog"

urlpatterns = [
    path("categories/", views.CategoryListCreateView.as_view(), name="category-list"),
    path(
        "categories/<uuid:category_id>/", views.CategoryDetailView.as_view(), name="category-detail"
    ),
    path("brands/", views.BrandListCreateView.as_view(), name="brand-list"),
    path("brands/<uuid:brand_id>/", views.BrandDetailView.as_view(), name="brand-detail"),
    path("products/", views.ProductListCreateView.as_view(), name="product-list"),
    path("products/<uuid:product_id>/", views.ProductDetailView.as_view(), name="product-detail"),
    path(
        "products/<uuid:product_id>/variants/",
        views.VariantListCreateView.as_view(),
        name="variant-list",
    ),
    path(
        "products/<uuid:product_id>/variants/<uuid:variant_id>/",
        views.VariantDetailView.as_view(),
        name="variant-detail",
    ),
]
