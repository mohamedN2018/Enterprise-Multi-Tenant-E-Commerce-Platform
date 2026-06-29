"""Rewards services: wallet, gift cards, loyalty.

All balance mutations acquire a row lock (``select_for_update``) and write an
append-only ledger entry. Gift-card redemption and loyalty redemption credit the
wallet; the wallet is debited when paying with the store-credit gateway.
"""

from __future__ import annotations

import secrets
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.db.models import F, Sum
from django.utils import timezone

from apps.core.exceptions import BusinessRuleError, ConflictError, ValidationError
from apps.core.services import BaseService, atomic
from apps.rewards.models import (
    GiftCard,
    GiftCardStatus,
    LoyaltyAccount,
    LoyaltyTransaction,
    LoyaltyTxnType,
    Referral,
    ReferralCode,
    ReferralStatus,
    Wallet,
    WalletTransaction,
    WalletTxnType,
)

_CENTS = Decimal("0.01")


def _money(value) -> Decimal:
    return Decimal(value).quantize(_CENTS, rounding=ROUND_HALF_UP)


class WalletService(BaseService):
    def get_or_create_wallet(self, *, store, user) -> Wallet:
        wallet, _ = Wallet.objects.get_or_create(
            store=store, user=user, defaults={"currency": store.currency}
        )
        return wallet

    def balance(self, *, store, user) -> Decimal:
        wallet = Wallet.objects.filter(store=store, user=user).first()
        return wallet.balance if wallet else Decimal("0.00")

    def history(self, *, store, user):
        wallet = Wallet.objects.filter(store=store, user=user).first()
        if wallet is None:
            return WalletTransaction.objects.none()
        return wallet.transactions.all()

    @atomic
    def credit(self, *, store, user, amount, reason: str = "", reference: str = "") -> Wallet:
        amount = _money(amount)
        if amount <= 0:
            raise ValidationError("Credit amount must be positive.")
        self.get_or_create_wallet(store=store, user=user)
        wallet = Wallet.objects.select_for_update().get(store=store, user=user)
        wallet.balance += amount
        wallet.save(update_fields=["balance", "updated_at"])
        self._log(store, wallet, WalletTxnType.CREDIT, amount, reason, reference)
        return wallet

    @atomic
    def debit(self, *, store, user, amount, reason: str = "", reference: str = "") -> Wallet:
        amount = _money(amount)
        if amount <= 0:
            raise ValidationError("Debit amount must be positive.")
        wallet = Wallet.objects.select_for_update().filter(store=store, user=user).first()
        if wallet is None or wallet.balance < amount:
            raise BusinessRuleError("Insufficient wallet balance.", code="insufficient_funds")
        wallet.balance -= amount
        wallet.save(update_fields=["balance", "updated_at"])
        self._log(store, wallet, WalletTxnType.DEBIT, amount, reason, reference)
        return wallet

    @staticmethod
    def _log(store, wallet, txn_type, amount, reason, reference) -> None:
        WalletTransaction.objects.create(
            store=store,
            wallet=wallet,
            txn_type=txn_type,
            amount=amount,
            balance_after=wallet.balance,
            reason=reason,
            reference=reference,
        )


class GiftCardService(BaseService):
    @atomic
    def issue(self, *, store, amount, code: str | None = None) -> GiftCard:
        amount = _money(amount)
        if amount <= 0:
            raise ValidationError("Gift card amount must be positive.")
        code = (code or secrets.token_hex(8)).strip().upper()
        if GiftCard.all_objects.filter(store=store, code=code, is_deleted=False).exists():
            raise ConflictError("A gift card with this code already exists.", code="code_taken")
        return GiftCard.objects.create(
            store=store, code=code, initial_balance=amount, balance=amount
        )

    @atomic
    def redeem(self, *, store, user, code: str) -> Decimal:
        card = (
            GiftCard.objects.select_for_update()
            .filter(store=store, code=code.strip().upper(), status=GiftCardStatus.ACTIVE)
            .first()
        )
        if card is None or card.balance <= 0:
            raise ValidationError(
                "This gift card is invalid or has no balance.", code="invalid_gift_card"
            )
        amount = card.balance
        card.balance = Decimal("0.00")
        card.status = GiftCardStatus.REDEEMED
        card.save(update_fields=["balance", "status", "updated_at"])
        WalletService().credit(
            store=store,
            user=user,
            amount=amount,
            reason="gift_card",
            reference=f"giftcard:{card.id}",
        )
        return amount


class LoyaltyService(BaseService):
    def get_or_create_account(self, *, store, user) -> LoyaltyAccount:
        account, _ = LoyaltyAccount.objects.get_or_create(store=store, user=user)
        return account

    def balance(self, *, store, user) -> int:
        account = LoyaltyAccount.objects.filter(store=store, user=user).first()
        return account.points if account else 0

    @atomic
    def earn(self, *, store, user, points: int, reason: str = "", reference: str = ""):
        if points <= 0:
            return None
        self.get_or_create_account(store=store, user=user)
        account = LoyaltyAccount.objects.select_for_update().get(store=store, user=user)
        account.points += points
        account.save(update_fields=["points", "updated_at"])
        self._log(store, account, LoyaltyTxnType.EARN, points, reason, reference)
        return account

    def earn_for_order(self, *, order) -> None:
        rate = Decimal(str(settings.REWARDS.get("LOYALTY_EARN_RATE", 0)))
        if rate <= 0:
            return
        points = int(order.total * rate)
        if points <= 0:
            return
        self.earn(
            store=order.store,
            user=order.user,
            points=points,
            reason="order",
            reference=f"order:{order.id}",
        )

    @atomic
    def redeem(self, *, store, user, points: int) -> dict:
        if points <= 0:
            raise ValidationError("Points to redeem must be positive.")
        account = LoyaltyAccount.objects.select_for_update().filter(store=store, user=user).first()
        if account is None or account.points < points:
            raise BusinessRuleError("Insufficient loyalty points.", code="insufficient_points")
        account.points -= points
        account.save(update_fields=["points", "updated_at"])
        self._log(store, account, LoyaltyTxnType.REDEEM, points, "redeem", "")
        rate = Decimal(str(settings.REWARDS.get("LOYALTY_REDEEM_RATE", "0.01")))
        credit_amount = _money(Decimal(points) * rate)
        WalletService().credit(
            store=store, user=user, amount=credit_amount, reason="loyalty_redeem"
        )
        return {
            "points_redeemed": points,
            "wallet_credit": credit_amount,
            "loyalty_balance": account.points,
        }

    @staticmethod
    def _log(store, account, txn_type, points, reason, reference) -> None:
        LoyaltyTransaction.objects.create(
            store=store,
            account=account,
            txn_type=txn_type,
            points=points,
            balance_after=account.points,
            reason=reason,
            reference=reference,
        )


class ReferralService(BaseService):
    """Referral codes + referrals; both parties credited on a qualifying order.

    Reward amounts and the qualifying-order threshold come from ``settings.REWARDS``
    (``REFERRER_REWARD`` / ``REFEREE_REWARD`` / ``REFERRAL_MIN_ORDER``); all default
    to 0, so the program is a no-op until configured.
    """

    @atomic
    def get_or_create_code(self, *, store, user) -> ReferralCode:
        existing = ReferralCode.objects.filter(store=store, user=user).first()
        if existing is not None:
            return existing
        return ReferralCode.objects.create(store=store, user=user, code=self._unique_code(store))

    @atomic
    def apply_code(self, *, store, referee, code: str) -> Referral:
        referral_code = ReferralCode.objects.filter(store=store, code=code.strip().upper()).first()
        if referral_code is None:
            raise ValidationError(
                "Invalid referral code.",
                code="invalid_referral_code",
                errors={"code": ["Invalid referral code."]},
            )
        if referral_code.user_id == referee.id:
            raise BusinessRuleError("You cannot use your own referral code.", code="self_referral")
        if Referral.objects.filter(store=store, referee=referee).exists():
            raise ConflictError("You have already been referred.", code="already_referred")
        if self._has_orders(store=store, user=referee):
            raise BusinessRuleError(
                "Referral codes are for new customers only.", code="existing_customer"
            )
        return Referral.objects.create(
            store=store, referrer=referral_code.user, referee=referee, code=referral_code.code
        )

    @atomic
    def reward_for_order(self, *, order) -> None:
        """Settle the referee's pending referral when their order qualifies."""
        referral = (
            Referral.objects.select_for_update()
            .filter(store=order.store, referee=order.user, status=ReferralStatus.PENDING)
            .first()
        )
        if referral is None:
            return
        min_order = _money(settings.REWARDS.get("REFERRAL_MIN_ORDER", "0.00"))
        if order.total < min_order:
            return
        referrer_reward = _money(settings.REWARDS.get("REFERRER_REWARD", "0.00"))
        referee_reward = _money(settings.REWARDS.get("REFEREE_REWARD", "0.00"))
        wallet = WalletService()
        reference = f"referral:{referral.id}"
        if referrer_reward > 0:
            wallet.credit(
                store=order.store,
                user=referral.referrer,
                amount=referrer_reward,
                reason="referral",
                reference=reference,
            )
        if referee_reward > 0:
            wallet.credit(
                store=order.store,
                user=referral.referee,
                amount=referee_reward,
                reason="referral",
                reference=reference,
            )
        referral.status = ReferralStatus.REWARDED
        referral.referrer_reward = referrer_reward
        referral.referee_reward = referee_reward
        referral.order = order
        referral.rewarded_at = timezone.now()
        referral.save(
            update_fields=[
                "status",
                "referrer_reward",
                "referee_reward",
                "order",
                "rewarded_at",
                "updated_at",
            ]
        )
        ReferralCode.objects.filter(store=order.store, user=referral.referrer).update(
            uses_count=F("uses_count") + 1
        )

    def list_made(self, *, store, user):
        return Referral.objects.filter(store=store, referrer=user).select_related("referee")

    def stats(self, *, store, user) -> dict:
        code = self.get_or_create_code(store=store, user=user)
        made = Referral.objects.filter(store=store, referrer=user)
        rewarded = made.filter(status=ReferralStatus.REWARDED)
        total_earned = rewarded.aggregate(total=Sum("referrer_reward"))["total"] or Decimal("0.00")
        return {
            "code": code.code,
            "total_referrals": made.count(),
            "rewarded": rewarded.count(),
            "pending": made.filter(status=ReferralStatus.PENDING).count(),
            "total_earned": str(_money(total_earned)),
        }

    @staticmethod
    def _has_orders(*, store, user) -> bool:
        from apps.orders.models import Order

        return Order.all_objects.filter(store=store, user=user, is_deleted=False).exists()

    @staticmethod
    def _unique_code(store) -> str:
        for _ in range(10):
            candidate = secrets.token_hex(4).upper()
            if not ReferralCode.all_objects.filter(
                store=store, code=candidate, is_deleted=False
            ).exists():
                return candidate
        return secrets.token_hex(8).upper()
