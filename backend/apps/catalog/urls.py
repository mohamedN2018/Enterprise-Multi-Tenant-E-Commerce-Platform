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
    path(
        "products/<uuid:product_id>/components/",
        views.BundleComponentListCreateView.as_view(),
        name="component-list",
    ),
    path(
        "products/<uuid:product_id>/components/<uuid:component_id>/",
        views.BundleComponentDetailView.as_view(),
        name="component-detail",
    ),
    # Digital products (staff)
    path(
        "variants/<uuid:variant_id>/digital/",
        views.DigitalAssetView.as_view(),
        name="variant-digital",
    ),
    path(
        "variants/<uuid:variant_id>/license-keys/",
        views.LicenseKeyListCreateView.as_view(),
        name="variant-license-keys",
    ),
    # Attributes & configurable products
    path("attributes/", views.AttributeListCreateView.as_view(), name="attribute-list"),
    path(
        "attributes/<uuid:attribute_id>/",
        views.AttributeDetailView.as_view(),
        name="attribute-detail",
    ),
    path(
        "attributes/<uuid:attribute_id>/values/",
        views.AttributeValueListCreateView.as_view(),
        name="attribute-values",
    ),
    path(
        "products/<uuid:product_id>/attributes/",
        views.ProductAttributeListCreateView.as_view(),
        name="product-attribute-list",
    ),
    path(
        "products/<uuid:product_id>/attributes/<uuid:product_attribute_id>/",
        views.ProductAttributeDetailView.as_view(),
        name="product-attribute-detail",
    ),
    path(
        "products/<uuid:product_id>/variants/<uuid:variant_id>/options/",
        views.VariantOptionsView.as_view(),
        name="variant-options",
    ),
    path(
        "products/<uuid:product_id>/generate-variants/",
        views.GenerateVariantMatrixView.as_view(),
        name="generate-variants",
    ),
]
