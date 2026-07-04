"""Pricing application service: groups, price rules, and price resolution."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from django.utils.text import slugify

from apps.accounts.repositories import UserRepository
from apps.catalog.models import ProductVariant
from apps.core.exceptions import ConflictError, NotFoundError, ValidationError
from apps.core.services import BaseService, atomic
from apps.pricing.models import (
    CustomerGroup,
    CustomerGroupMembership,
    PriceRule,
    PriceRuleType,
)
from apps.pricing.repositories import CustomerGroupRepository

_CENTS = Decimal("0.01")


def _money(value) -> Decimal:
    return Decimal(value).quantize(_CENTS, rounding=ROUND_HALF_UP)


class PricingService(BaseService):
    def __init__(self, group_repo: CustomerGroupRepository | None = None) -> None:
        self.group_repo = group_repo or CustomerGroupRepository()

    # --- Price resolution (used by the cart) ---
    def resolve_price(self, *, store, variant, user, quantity: int) -> Decimal:
        """Return the best (lowest) applicable unit price, capped at the base price."""
        base = variant.price
        group = self._buyer_group(store=store, user=user)
        group_id = group.id if group else None

        best = base
        rules = PriceRule.objects.filter(
            variant=variant, is_active=True, min_quantity__lte=quantity
        )
        for rule in rules:
            if rule.customer_group_id is not None and rule.customer_group_id != group_id:
                continue
            price = self._rule_price(rule, base)
            if price < best:
                best = price
        return _money(best)

    def _buyer_group(self, *, store, user) -> CustomerGroup | None:
        if user is not None and getattr(user, "is_authenticated", False):
            membership = (
                CustomerGroupMembership.objects.filter(store=store, user=user)
                .select_related("customer_group")
                .first()
            )
            if membership is not None:
                return membership.customer_group
        return CustomerGroup.objects.filter(store=store, is_default=True).first()

    @staticmethod
    def _rule_price(rule: PriceRule, base: Decimal) -> Decimal:
        # Clamp defensively so a malformed rule (e.g. a >100% discount) can never
        # yield a negative unit price that would credit the buyer at checkout.
        if rule.rule_type == PriceRuleType.PERCENT_DISCOUNT:
            pct = max(Decimal("0"), min(rule.value, Decimal("100")))
            return base * (Decimal("1") - pct / Decimal("100"))
        return max(rule.value, Decimal("0"))

    # --- Customer groups ---
    @atomic
    def create_group(self, *, store, data: dict) -> CustomerGroup:
        code = data.get("code")
        if code:
            if self.group_repo.code_exists(store=store, code=code):
                raise ConflictError("A group with this code already exists.", code="code_taken")
        else:
            code = self._unique_code(store=store, name=data["name"])
        payload = {k: v for k, v in data.items() if k != "code"}
        group = CustomerGroup.objects.create(store=store, code=code, **payload)
        if group.is_default:
            self._clear_other_defaults(store=store, keep=group)
        return group

    @atomic
    def update_group(self, *, instance: CustomerGroup, data: dict) -> CustomerGroup:
        for field, value in data.items():
            setattr(instance, field, value)
        instance.save()
        if instance.is_default:
            self._clear_other_defaults(store=instance.store, keep=instance)
        return instance

    @staticmethod
    def _clear_other_defaults(*, store, keep: CustomerGroup) -> None:
        CustomerGroup.objects.filter(store=store, is_default=True).exclude(pk=keep.pk).update(
            is_default=False
        )

    def _unique_code(self, *, store, name: str) -> str:
        base = slugify(name)[:110] or "group"
        code = base
        suffix = 1
        while self.group_repo.code_exists(store=store, code=code):
            suffix += 1
            code = f"{base}-{suffix}"
        return code

    # --- Memberships ---
    def list_members(self, group: CustomerGroup):
        return group.memberships.select_related("user")

    @atomic
    def assign_member(self, *, store, group: CustomerGroup, email: str) -> CustomerGroupMembership:
        user = UserRepository().get_by_email(email)
        if user is None:
            raise ValidationError(
                "No user found with this email address.",
                code="user_not_found",
                errors={"email": ["No user found with this email address."]},
            )
        membership, _ = CustomerGroupMembership.objects.update_or_create(
            store=store, user=user, defaults={"customer_group": group}
        )
        return membership

    @atomic
    def remove_member(self, *, group: CustomerGroup, user_id) -> None:
        membership = group.memberships.filter(user_id=user_id).first()
        if membership is None:
            raise NotFoundError("Membership not found.")
        membership.delete()

    # --- Price rules ---
    @atomic
    def create_rule(self, *, store, data: dict) -> PriceRule:
        variant = ProductVariant.objects.filter(id=data["variant_id"]).first()
        if variant is None:
            raise ValidationError(
                "Variant not found in this store.",
                code="variant_not_found",
                errors={"variant_id": ["Not found in this store."]},
            )
        group = None
        if data.get("customer_group_id"):
            group = CustomerGroup.objects.filter(id=data["customer_group_id"]).first()
            if group is None:
                raise ValidationError(
                    "Customer group not found in this store.",
                    code="group_not_found",
                    errors={"customer_group_id": ["Not found in this store."]},
                )
        return PriceRule.objects.create(
            store=store,
            variant=variant,
            customer_group=group,
            min_quantity=data.get("min_quantity", 1),
            rule_type=data.get("rule_type", PriceRuleType.FIXED),
            value=data["value"],
            is_active=data.get("is_active", True),
        )

    @atomic
    def update_rule(self, *, instance: PriceRule, data: dict) -> PriceRule:
        for field in ("min_quantity", "rule_type", "value", "is_active"):
            if field in data:
                setattr(instance, field, data[field])
        instance.save()
        return instance
