"""Pluggable fraud risk engine.

Each rule inspects an order (plus its store/user context) and returns a
``(score, reason)`` pair — a positive score with a human-readable reason when it
fires, or ``(0, None)`` otherwise. :class:`RiskEngine` sums the contributions.
Rules are configured (and individually disabled) via ``settings.FRAUD``; with the
shipped defaults every rule is off, so the engine scores 0 and orders approve.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.utils import timezone


def _cfg() -> dict:
    return settings.FRAUD


def _high_value(order, cfg) -> tuple[int, str | None]:
    threshold = Decimal(str(cfg.get("HIGH_VALUE_THRESHOLD", "0")))
    if threshold > 0 and order.total >= threshold:
        return int(
            cfg.get("HIGH_VALUE_SCORE", 40)
        ), f"High order value ({order.total} >= {threshold})"
    return 0, None


def _velocity(order, cfg) -> tuple[int, str | None]:
    max_orders = int(cfg.get("VELOCITY_MAX_ORDERS", 0))
    if max_orders <= 0:
        return 0, None
    window = int(cfg.get("VELOCITY_WINDOW_MINUTES", 10))
    since = timezone.now() - timedelta(minutes=window)
    from apps.orders.models import Order

    count = Order.all_objects.filter(
        store=order.store, user=order.user, is_deleted=False, placed_at__gte=since
    ).count()
    if count > max_orders:
        return int(cfg.get("VELOCITY_SCORE", 40)), f"{count} orders within {window} minutes"
    return 0, None


def _new_account(order, cfg) -> tuple[int, str | None]:
    minutes = int(cfg.get("NEW_ACCOUNT_MINUTES", 0))
    if minutes <= 0:
        return 0, None
    cutoff = timezone.now() - timedelta(minutes=minutes)
    if order.user.created_at >= cutoff:
        return int(cfg.get("NEW_ACCOUNT_SCORE", 30)), "Account created recently"
    return 0, None


RULES = (_high_value, _velocity, _new_account)


class RiskEngine:
    def evaluate(self, order) -> tuple[int, list[str]]:
        cfg = _cfg()
        score = 0
        reasons: list[str] = []
        for rule in RULES:
            contribution, reason = rule(order, cfg)
            if contribution > 0 and reason:
                score += contribution
                reasons.append(reason)
        return score, reasons
