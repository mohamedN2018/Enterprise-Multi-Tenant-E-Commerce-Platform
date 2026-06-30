"""Admin registration for payments."""

from __future__ import annotations

from django.contrib import admin

from apps.payments.models import Payment, PaymentEvent


class PaymentEventInline(admin.TabularInline):
    model = PaymentEvent
    extra = 0
    readonly_fields = ("event_type", "message", "data", "created_at")
    can_delete = False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "gateway", "amount", "currency", "status", "paid_at")
    list_filter = ("status", "gateway", "currency")
    search_fields = ("order__number", "transaction_id", "user__email")
    readonly_fields = ("transaction_id", "paid_at", "amount", "currency")
    inlines = (PaymentEventInline,)
