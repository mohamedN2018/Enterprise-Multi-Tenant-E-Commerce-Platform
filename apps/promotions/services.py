"""Promotion application service: coupon validation, discount, redemption."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from django.db.models import F

from apps.core.exceptions import BusinessRuleError, ConflictError, ValidationError
from apps.core.services import BaseService, atomic
from apps.promotions.models import Coupon, CouponRedemption, DiscountType
from apps.promotions.repositories import CouponRepository

_CENTS = Decimal("0.01")


def _money(value) -> Decimal:
    return Decimal(value).quantize(_CENTS, rounding=ROUND_HALF_UP)


class PromotionService(BaseService):
    def __init__(self, repository: CouponRepository | None = None) -> None:
        self.repository = repository or CouponRepository()

    # --- Coupon management (staff) ---
    @atomic
    def create_coupon(self, *, store, data: dict) -> Coupon:
        code = data["code"].strip().upper()
        if self.repository.code_exists(store=store, code=code):
            raise ConflictError("A coupon with this code already exists.", code="code_taken")
        return Coupon.objects.create(store=store, **{**data, "code": code})

    @atomic
    def update_coupon(self, *, instance: Coupon, data: dict) -> Coupon:
        if "code" in data:
            data = {**data, "code": data["code"].strip().upper()}
            if self.repository.code_exists(
                store=instance.store, code=data["code"], exclude_pk=instance.pk
            ):
                raise ConflictError("A coupon with this code already exists.", code="code_taken")
        for field, value in data.items():
            setattr(instance, field, value)
        instance.save()
        return instance

    # --- Validation & discount ---
    def find_active(self, *, store, code: str) -> Coupon | None:
        return Coupon.objects.filter(store=store, code=code.strip().upper(), is_active=True).first()

    def validate(self, *, store, code: str, user, subtotal: Decimal) -> Coupon:
        coupon = self.find_active(store=store, code=code)
        if coupon is None:
            raise ValidationError(
                "Invalid coupon code.",
                code="coupon_invalid",
                errors={"code": ["Invalid coupon code."]},
            )
        self._assert_usable(coupon=coupon, user=user, subtotal=subtotal)
        return coupon

    def _assert_usable(self, *, coupon: Coupon, user, subtotal: Decimal) -> None:
        if not coupon.is_within_window():
            raise BusinessRuleError("This coupon is not currently valid.", code="coupon_expired")
        if not coupon.has_global_capacity():
            raise BusinessRuleError(
                "This coupon has reached its usage limit.", code="coupon_exhausted"
            )
        if coupon.min_spend is not None and subtotal < coupon.min_spend:
            raise BusinessRuleError(
                f"A minimum spend of {coupon.min_spend} is required to use this coupon.",
                code="min_spend_not_met",
            )
        if coupon.per_user_limit is not None:
            used = CouponRedemption.objects.filter(coupon=coupon, user=user).count()
            if used >= coupon.per_user_limit:
                raise BusinessRuleError(
                    "You have already used this coupon the maximum number of times.",
                    code="per_user_limit_reached",
                )

    def compute_discount(self, *, coupon: Coupon, subtotal: Decimal) -> Decimal:
        if coupon.discount_type == DiscountType.PERCENTAGE:
            discount = subtotal * coupon.value / Decimal("100")
            if coupon.max_discount is not None:
                discount = min(discount, coupon.max_discount)
        else:
            discount = coupon.value
        return _money(min(discount, subtotal))

    def quote(self, *, store, code: str, user, subtotal: Decimal) -> tuple[Coupon, Decimal]:
        coupon = self.validate(store=store, code=code, user=user, subtotal=subtotal)
        return coupon, self.compute_discount(coupon=coupon, subtotal=subtotal)

    @atomic
    def redeem(self, *, store, coupon: Coupon, user, order, amount: Decimal) -> CouponRedemption:
        Coupon.objects.filter(pk=coupon.pk).update(used_count=F("used_count") + 1)
        return CouponRedemption.objects.create(
            store=store, coupon=coupon, user=user, order=order, amount=amount
        )
