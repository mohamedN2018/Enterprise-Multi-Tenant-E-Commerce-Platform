"""Analytics application service: record events + roll up store summaries."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Count, Sum

from apps.analytics.models import AnalyticsEvent
from apps.core.services import BaseService, atomic

_CENTS = Decimal("0.01")


class AnalyticsService(BaseService):
    @atomic
    def record(
        self, *, store, event_type: str, user=None, data: dict | None = None, occurred_at=None
    ) -> AnalyticsEvent:
        fields = {"store": store, "event_type": event_type, "user": user, "data": data or {}}
        if occurred_at is not None:
            fields["occurred_at"] = occurred_at
        return AnalyticsEvent.objects.create(**fields)

    def summary(self, *, store, start=None, end=None) -> dict:
        """Roll up events (counts by type) and order metrics over an optional window."""
        events = AnalyticsEvent.objects.filter(store=store)
        if start is not None:
            events = events.filter(occurred_at__gte=start)
        if end is not None:
            events = events.filter(occurred_at__lte=end)
        events_by_type = {
            row["event_type"]: row["count"]
            for row in events.values("event_type").annotate(count=Count("id")).order_by()
        }

        from apps.orders.models import Order, OrderStatus

        orders = Order.objects.filter(store=store)
        if start is not None:
            orders = orders.filter(placed_at__gte=start)
        if end is not None:
            orders = orders.filter(placed_at__lte=end)
        confirmed = orders.filter(status=OrderStatus.CONFIRMED)
        revenue = confirmed.aggregate(total=Sum("total"))["total"] or Decimal("0.00")

        return {
            "events": events_by_type,
            "total_events": sum(events_by_type.values()),
            "orders": {
                "count": orders.count(),
                "confirmed": confirmed.count(),
                "revenue": str(revenue.quantize(_CENTS, rounding=ROUND_HALF_UP)),
            },
        }
