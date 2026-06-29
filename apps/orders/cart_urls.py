"""Cart API routes (mounted under /api/v1/cart/). Store via header."""

from django.urls import path

from apps.orders import views

app_name = "cart"

urlpatterns = [
    path("", views.CartView.as_view(), name="cart"),
    path("items/", views.CartItemCreateView.as_view(), name="item-add"),
    path("items/<uuid:item_id>/", views.CartItemDetailView.as_view(), name="item-detail"),
    path("checkout/", views.CheckoutView.as_view(), name="checkout"),
]
