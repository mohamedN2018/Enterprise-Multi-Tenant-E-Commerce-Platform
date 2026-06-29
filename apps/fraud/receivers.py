"""Domain-signal receiver: risk-score every placed order.

Connected in :class:`apps.fraud.apps.FraudConfig.ready`. Runs inside checkout's
transaction so the assessment commits (or rolls back) with the order.
"""

from __future__ import annotations

from django.dispatch import receiver

from apps.core.signals import order_placed
from apps.fraud.services import FraudService


@receiver(order_placed, dispatch_uid="fraud.assess_on_placed")
def on_order_placed(sender, order, **kwargs) -> None:
    FraudService().assess(order=order)
