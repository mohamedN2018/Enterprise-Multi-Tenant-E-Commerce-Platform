"""Domain-signal receivers: turn order-lifecycle events into buyer notifications.

Connected in :class:`apps.notifications.apps.NotificationsConfig.ready`. Keeping
these here (rather than in ``orders``) preserves the producer/consumer
decoupling: ``orders`` emits, ``notifications`` listens.
"""

from __future__ import annotations

from django.dispatch import receiver

from apps.core.signals import order_cancelled, order_confirmed, order_placed
from apps.notifications.services import NotificationService


def _notify(order, *, event_type: str, title: str, body: str) -> None:
    NotificationService().notify(
        store=order.store,
        recipient=order.user,
        event_type=event_type,
        title=title,
        body=body,
        data={"order_id": str(order.id), "number": order.number},
    )


@receiver(order_placed, dispatch_uid="notifications.order_placed")
def on_order_placed(sender, order, **kwargs) -> None:
    _notify(
        order,
        event_type="order.placed",
        title=f"Order {order.number} placed",
        body="We've received your order and it is now pending.",
    )


@receiver(order_confirmed, dispatch_uid="notifications.order_confirmed")
def on_order_confirmed(sender, order, **kwargs) -> None:
    _notify(
        order,
        event_type="order.confirmed",
        title=f"Order {order.number} confirmed",
        body="Your order has been confirmed and is being prepared.",
    )


@receiver(order_cancelled, dispatch_uid="notifications.order_cancelled")
def on_order_cancelled(sender, order, **kwargs) -> None:
    _notify(
        order,
        event_type="order.cancelled",
        title=f"Order {order.number} cancelled",
        body="Your order has been cancelled.",
    )
