"""Automatic promotion engine (campaigns).

Given a store, the cart lines and the subtotal, :class:`PromotionEngine` evaluates
every *live* campaign and returns a single :class:`PromotionResult` with the total
automatic discount and whether shipping should be free. It is intentionally
read-only — it computes, it does not persist — so both the cart preview and
checkout can call it. With no campaigns configured it returns a zero result, which
keeps checkout (and all prior tests) unchanged.

A "line" is any object exposing ``variant.product_id``, ``quantity`` and
``unit_price`` (both ``CartItem`` and ``OrderItem`` qualify).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Q
from django.utils import timezone

from apps.core.services import BaseService
from apps.promotions.models import Campaign, CampaignType, DiscountType


def live_campaigns_qs(store):
    """Store campaigns that are active and within their validity window, now."""
    now = timezone.now()
    return (
        Campaign.objects.filter(store=store, is_active=True)
        .filter(Q(starts_at__isnull=True) | Q(starts_at__lte=now))
        .filter(Q(ends_at__isnull=True) | Q(ends_at__gte=now))
        .order_by("-priority", "created_at")
    )


_CENTS = Decimal("0.01")
_ZERO = Decimal("0.00")


def _money(value) -> Decimal:
    return Decimal(value).quantize(_CENTS, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class PromotionResult:
    discount: Decimal = _ZERO
    free_shipping: bool = False
    applied: list[str] = field(default_factory=list)


class PromotionEngine(BaseService):
    def evaluate(self, *, store, items, subtotal: Decimal) -> PromotionResult:
        items = list(items)
        discount = _ZERO
        free_shipping = False
        applied: list[str] = []
        discount_count = 0
        discount_locked = False

        for campaign in self._live_campaigns(store):
            if campaign.campaign_type == CampaignType.FREE_SHIPPING:
                if subtotal >= (campaign.min_spend or _ZERO):
                    free_shipping = True
                    applied.append(campaign.name)
                continue

            if discount_locked:
                continue
            # A non-stackable campaign cannot pile onto an already-applied discount.
            if not campaign.stackable and discount_count > 0:
                continue

            amount = self._discount_for(campaign, items=items, subtotal=subtotal)
            if amount <= 0:
                continue
            discount += amount
            discount_count += 1
            applied.append(campaign.name)
            if not campaign.stackable:
                discount_locked = True  # exclusive: blocks further discounts

        return PromotionResult(
            discount=_money(min(discount, subtotal)),
            free_shipping=free_shipping,
            applied=applied,
        )

    # --- Internals ---
    def _live_campaigns(self, store) -> list[Campaign]:
        return list(live_campaigns_qs(store).prefetch_related("products"))

    def _discount_for(self, campaign: Campaign, *, items, subtotal: Decimal) -> Decimal:
        if campaign.campaign_type == CampaignType.ORDER_DISCOUNT:
            return self._order_discount(campaign, subtotal=subtotal)
        matching = self._matching_lines(campaign, items=items)
        if not matching:
            return _ZERO
        if campaign.campaign_type == CampaignType.FLASH_SALE:
            return self._flash_sale(campaign, matching=matching)
        if campaign.campaign_type == CampaignType.BUY_X_GET_Y:
            return self._buy_x_get_y(campaign, matching=matching)
        return _ZERO

    @staticmethod
    def _matching_lines(campaign: Campaign, *, items) -> list:
        product_ids = {cp.product_id for cp in campaign.products.all()}
        if not product_ids:
            return []
        return [item for item in items if item.variant.product_id in product_ids]

    @staticmethod
    def _order_discount(campaign: Campaign, *, subtotal: Decimal) -> Decimal:
        if subtotal < (campaign.min_spend or _ZERO):
            return _ZERO
        value = campaign.discount_value or _ZERO
        if campaign.discount_type == DiscountType.PERCENTAGE:
            amount = subtotal * value / Decimal("100")
            if campaign.max_discount is not None:
                amount = min(amount, campaign.max_discount)
        else:
            amount = value
        return _money(min(amount, subtotal))

    @staticmethod
    def _flash_sale(campaign: Campaign, *, matching) -> Decimal:
        matched_subtotal = sum((item.unit_price * item.quantity for item in matching), _ZERO)
        value = campaign.discount_value or _ZERO
        if campaign.discount_type == DiscountType.PERCENTAGE:
            amount = matched_subtotal * value / Decimal("100")
        else:
            # Fixed amount off each matching unit, never below free.
            amount = sum((min(value, item.unit_price) * item.quantity for item in matching), _ZERO)
        amount = min(amount, matched_subtotal)
        if campaign.max_discount is not None:
            amount = min(amount, campaign.max_discount)
        return _money(amount)

    @staticmethod
    def _buy_x_get_y(campaign: Campaign, *, matching) -> Decimal:
        group = (campaign.buy_quantity or 0) + (campaign.get_quantity or 0)
        if group <= 0 or not campaign.get_quantity:
            return _ZERO
        units: list[Decimal] = []
        for item in matching:
            units.extend([item.unit_price] * item.quantity)
        free_units = (len(units) // group) * campaign.get_quantity
        if free_units <= 0:
            return _ZERO
        units.sort()  # the cheapest qualifying units are the discounted ones
        percent = (campaign.get_discount_percent or _ZERO) / Decimal("100")
        amount = sum((price * percent for price in units[:free_units]), _ZERO)
        return _money(amount)
