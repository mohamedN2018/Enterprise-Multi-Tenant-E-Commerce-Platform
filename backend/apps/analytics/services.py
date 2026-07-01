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

    def dashboard(self, *, store) -> dict:
        """A rich, store-wide snapshot for the admin dashboard."""
        from datetime import timedelta

        from django.db.models import Avg, F, Sum
        from django.db.models.functions import TruncDate
        from django.utils import timezone

        from apps.catalog.models import Category, Product, ProductStatus
        from apps.fraud.models import FraudCheck
        from apps.inventory.models import StockItem
        from apps.orders.models import Order, OrderItem, OrderStatus
        from apps.payouts.models import SellerAccount
        from apps.returns.models import ReturnRequest, ReturnStatus
        from apps.reviews.models import Review, ReviewStatus

        orders = Order.objects.filter(store=store)
        by_status = {
            r["status"]: r["count"] for r in orders.values("status").annotate(count=Count("id"))
        }
        confirmed = orders.filter(status=OrderStatus.CONFIRMED)
        revenue = confirmed.aggregate(t=Sum("total"))["t"] or Decimal("0.00")
        confirmed_count = by_status.get(OrderStatus.CONFIRMED, 0)
        aov = (revenue / confirmed_count) if confirmed_count else Decimal("0.00")

        threshold = getattr(getattr(store, "settings", None), "low_stock_threshold", 0) or 0
        low_stock = (
            StockItem.objects.filter(
                store=store, quantity__lte=F("reserved_quantity") + threshold
            ).count()
            if threshold
            else 0
        )

        seller = SellerAccount.objects.filter(store=store).first()

        recent_orders = [
            {
                "number": o.number,
                "status": o.status,
                "total": str(o.total),
                "currency": o.currency,
                "created_at": o.created_at.isoformat(),
            }
            for o in orders.order_by("-created_at")[:6]
        ]

        top_products = [
            {
                "name": t["product_name"],
                "units": t["units"],
                "revenue": str(t["revenue"] or Decimal("0.00")),
            }
            for t in (
                OrderItem.objects.filter(store=store, order__status=OrderStatus.CONFIRMED)
                .values("product_name")
                .annotate(units=Sum("quantity"), revenue=Sum("line_total"))
                .order_by("-units")[:5]
            )
        ]

        today = timezone.now().date()
        start = today - timedelta(days=13)
        daily = {
            r["day"]: r["total"]
            for r in confirmed.filter(placed_at__date__gte=start)
            .annotate(day=TruncDate("placed_at"))
            .values("day")
            .annotate(total=Sum("total"))
        }
        revenue_series = [
            {
                "date": (start + timedelta(days=i)).isoformat(),
                "revenue": str(daily.get(start + timedelta(days=i)) or Decimal("0.00")),
            }
            for i in range(14)
        ]

        events = {
            r["event_type"]: r["count"]
            for r in AnalyticsEvent.objects.filter(store=store)
            .values("event_type")
            .annotate(count=Count("id"))
            .order_by()
        }
        avg_rating = Review.objects.filter(store=store, status=ReviewStatus.APPROVED).aggregate(
            a=Avg("rating")
        )["a"]

        return {
            "orders": {
                "count": orders.count(),
                "pending": by_status.get(OrderStatus.PENDING, 0),
                "confirmed": confirmed_count,
                "cancelled": by_status.get(OrderStatus.CANCELLED, 0),
                "revenue": str(revenue.quantize(_CENTS, rounding=ROUND_HALF_UP)),
                "aov": str(aov.quantize(_CENTS, rounding=ROUND_HALF_UP)),
            },
            "catalog": {
                "products": Product.objects.filter(store=store).count(),
                "published": Product.objects.filter(
                    store=store, status=ProductStatus.PUBLISHED
                ).count(),
                "categories": Category.objects.filter(store=store).count(),
                "low_stock": low_stock,
            },
            "customers": orders.values("user").distinct().count(),
            "reviews": {
                "pending": Review.objects.filter(store=store, status=ReviewStatus.PENDING).count(),
                "average": round(float(avg_rating or 0), 2),
            },
            "fraud_pending": FraudCheck.objects.filter(store=store, resolution="pending").count(),
            "returns_pending": ReturnRequest.objects.filter(
                store=store, status=ReturnStatus.REQUESTED
            ).count(),
            "payout_balance": str(seller.balance) if seller else "0.00",
            "payout_currency": (seller.currency if seller else store.currency),
            "recent_orders": recent_orders,
            "top_products": top_products,
            "revenue_series": revenue_series,
            "events": events,
            "total_events": sum(events.values()),
        }
