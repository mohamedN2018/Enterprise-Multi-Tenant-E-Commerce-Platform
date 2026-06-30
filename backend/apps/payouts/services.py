"""Seller payout & commission service.

Balance mutations take a row lock (``select_for_update``) and write an
append-only ledger entry, mirroring the wallet pattern. Order earnings are
recorded once per order (idempotent) from the ``order_confirmed`` signal.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.utils import timezone

from apps.core.exceptions import BusinessRuleError, ConflictError, ValidationError
from apps.core.services import BaseService, atomic
from apps.payouts.models import (
    LedgerEntry,
    LedgerEntryType,
    Payout,
    PayoutStatus,
    SellerAccount,
)

_CENTS = Decimal("0.01")


def _money(value) -> Decimal:
    return Decimal(value).quantize(_CENTS, rounding=ROUND_HALF_UP)


def _default_rate() -> Decimal:
    return Decimal(str(settings.PAYOUTS.get("DEFAULT_COMMISSION_RATE", "0")))


class PayoutService(BaseService):
    def get_account(self, *, store) -> SellerAccount:
        account, _ = SellerAccount.objects.get_or_create(
            store=store,
            defaults={"currency": store.currency, "commission_rate": _default_rate()},
        )
        return account

    def balance(self, *, store) -> Decimal:
        account = SellerAccount.objects.filter(store=store).first()
        return account.balance if account else Decimal("0.00")

    def ledger(self, *, store):
        return LedgerEntry.objects.filter(store=store)

    @atomic
    def set_commission_rate(self, *, store, rate) -> SellerAccount:
        rate = _money(rate)
        if rate < 0 or rate > 100:
            raise ValidationError("Commission rate must be between 0 and 100.", code="invalid_rate")
        account = self.get_account(store=store)
        account.commission_rate = rate
        account.save(update_fields=["commission_rate", "updated_at"])
        return account

    @atomic
    def record_order_earning(self, *, order) -> LedgerEntry | None:
        # Idempotent: never double-credit the same order.
        if LedgerEntry.all_objects.filter(
            order=order, entry_type=LedgerEntryType.EARNING, is_deleted=False
        ).exists():
            return None
        self.get_account(store=order.store)
        account = SellerAccount.objects.select_for_update().get(store=order.store)
        gross = _money(order.total)
        commission = _money(gross * account.commission_rate / Decimal("100"))
        net = _money(gross - commission)
        account.balance += net
        account.save(update_fields=["balance", "updated_at"])
        return LedgerEntry.objects.create(
            store=order.store,
            account=account,
            entry_type=LedgerEntryType.EARNING,
            order=order,
            gross_amount=gross,
            commission_amount=commission,
            net_amount=net,
            balance_after=account.balance,
            reference=f"order:{order.id}",
        )

    @atomic
    def request_payout(self, *, store, amount) -> Payout:
        amount = _money(amount)
        if amount <= 0:
            raise ValidationError("Payout amount must be positive.")
        self.get_account(store=store)
        account = SellerAccount.objects.select_for_update().get(store=store)
        if account.balance < amount:
            raise BusinessRuleError(
                "Insufficient balance for this payout.", code="insufficient_balance"
            )
        account.balance -= amount
        account.save(update_fields=["balance", "updated_at"])
        payout = Payout.objects.create(store=store, amount=amount, status=PayoutStatus.PENDING)
        LedgerEntry.objects.create(
            store=store,
            account=account,
            entry_type=LedgerEntryType.PAYOUT,
            gross_amount=amount,
            net_amount=-amount,
            balance_after=account.balance,
            reference=f"payout:{payout.id}",
        )
        return payout

    @atomic
    def mark_paid(self, *, payout: Payout) -> Payout:
        if payout.status != PayoutStatus.PENDING:
            raise ConflictError("Only a pending payout can be marked paid.", code="not_pending")
        payout.status = PayoutStatus.PAID
        payout.paid_at = timezone.now()
        payout.save(update_fields=["status", "paid_at", "updated_at"])
        return payout

    def get_payout(self, *, store, payout_id) -> Payout:
        payout = Payout.objects.filter(store=store, id=payout_id).first()
        if payout is None:
            from apps.core.exceptions import NotFoundError

            raise NotFoundError("Payout not found.")
        return payout
