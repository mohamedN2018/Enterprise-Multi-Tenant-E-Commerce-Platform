"""Domain-signal receivers: record order-lifecycle events for analytics.

Connected in :class:`apps.analytics.apps.AnalyticsConfig.ready`.
"""

from __future__ import annotations

from django.dispatch import receiver

from apps.analytics.services import AnalyticsService
from apps.core.signals import order_cancelled, order_confirmed, order_placed


def _record(order, *, event_type: str) -> None:
    AnalyticsService().record(
        store=order.store,
        event_type=event_type,
        user=order.user,
        data={
            "order_id": str(order.id),
            "number": order.number,
            "total": str(order.total),
            "currency": order.currency,
        },
    )


@receiver(order_placed, dispatch_uid="analytics.order_placed")
def on_order_placed(sender, order, **kwargs) -> None:
    _record(order, event_type="order.placed")


@receiver(order_confirmed, dispatch_uid="analytics.order_confirmed")
def on_order_confirmed(sender, order, **kwargs) -> None:
    _record(order, event_type="order.confirmed")


@receiver(order_cancelled, dispatch_uid="analytics.order_cancelled")
def on_order_cancelled(sender, order, **kwargs) -> None:
    _record(order, event_type="order.cancelled")
