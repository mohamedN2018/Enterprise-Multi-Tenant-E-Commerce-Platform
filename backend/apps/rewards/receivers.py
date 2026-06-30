"""Domain-signal receivers: settle a referee's referral on order confirmation.

Connected in :class:`apps.rewards.apps.RewardsConfig.ready`. A no-op unless the
referee has a pending referral and the order meets the configured threshold.
"""

from __future__ import annotations

from django.dispatch import receiver

from apps.core.signals import order_confirmed
from apps.rewards.services import ReferralService


@receiver(order_confirmed, dispatch_uid="rewards.referral_on_confirm")
def on_order_confirmed(sender, order, **kwargs) -> None:
    ReferralService().reward_for_order(order=order)
