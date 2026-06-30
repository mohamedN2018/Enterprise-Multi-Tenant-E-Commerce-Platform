"""Domain-signal receiver: credit the seller's account on order confirmation.

Connected in :class:`apps.payouts.apps.PayoutsConfig.ready`. Idempotent and a
no-op for the seller's economics when the commission rate is the default 0
(the seller simply earns the full order total).
"""

from __future__ import annotations

from django.dispatch import receiver

from apps.core.signals import order_confirmed
from apps.payouts.services import PayoutService


@receiver(order_confirmed, dispatch_uid="payouts.earn_on_confirm")
def on_order_confirmed(sender, order, **kwargs) -> None:
    PayoutService().record_order_earning(order=order)
