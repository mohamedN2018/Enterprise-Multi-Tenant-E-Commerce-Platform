"""Admin registration for the ordering domain."""

from __future__ import annotations

from django.contrib import admin

from apps.orders.models import Cart, CartItem, Order, OrderItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ("variant", "quantity", "unit_price")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "store", "user", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("store__name", "user__email")
    inlines = (CartItemInline,)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("variant", "product_name", "sku", "unit_price", "quantity", "line_total")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "store", "user", "status", "total", "currency", "placed_at")
    list_filter = ("status", "currency")
    search_fields = ("number", "store__name", "user__email")
    readonly_fields = ("number", "subtotal", "tax_total", "total", "placed_at")
    inlines = (OrderItemInline,)
