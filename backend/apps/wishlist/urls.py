"""Wishlist API routes (mounted under /api/v1/wishlist/). Store via header."""

from django.urls import path

from apps.wishlist import views

app_name = "wishlist"

urlpatterns = [
    path("", views.WishlistListCreateView.as_view(), name="list"),
    path("<uuid:item_id>/", views.WishlistItemDetailView.as_view(), name="detail"),
    path(
        "<uuid:item_id>/move-to-cart/",
        views.WishlistMoveToCartView.as_view(),
        name="move-to-cart",
    ),
]
