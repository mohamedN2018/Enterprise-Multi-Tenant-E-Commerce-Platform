"""Public storefront routes (mounted under /api/v1/storefront/). No auth."""

from django.urls import path

from apps.storefront import views

app_name = "storefront"

urlpatterns = [
    path("stores/", views.StorefrontStoreListView.as_view(), name="stores"),
    path("stores/<slug:slug>/", views.StorefrontStoreDetailView.as_view(), name="store-detail"),
    path(
        "stores/<slug:slug>/products/",
        views.StorefrontProductListView.as_view(),
        name="store-products",
    ),
    path("categories/", views.StorefrontCategoryListView.as_view(), name="categories"),
    path("products/", views.StorefrontAllProductsView.as_view(), name="products"),
    path(
        "products/<uuid:product_id>/",
        views.StorefrontProductDetailView.as_view(),
        name="product-detail",
    ),
]
