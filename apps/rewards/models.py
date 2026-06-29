"""Rewards domain models (store-scoped): wallet, gift cards, loyalty.

* ``Wallet`` / ``WalletTransaction``     — a buyer's store-credit balance + ledger.
* ``GiftCard``                           — a redeemable balance that tops up a wallet.
* ``LoyaltyAccount`` / ``LoyaltyTransaction`` — points earned on orders, redeemable
  into wallet credit.

Referral rewards are a planned follow-up (P2.6b).
"""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.models import TenantOwnedModel


class Wallet(TenantOwnedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallets"
    )
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="USD")

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Wallet"
        verbose_name_plural = "Wallets"
        constraints = [
            models.UniqueConstraint(
                fields=["store", "user"],
                condition=Q(is_deleted=False),
                name="uniq_wallet_per_store_user",
            )
        ]

    def __str__(self) -> str:
        return f"Wallet({self.user_id}): {self.balance} {self.currency}"


class WalletTxnType(models.TextChoices):
    CREDIT = "credit", "Credit"
    DEBIT = "debit", "Debit"


class WalletTransaction(TenantOwnedModel):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    txn_type = models.CharField(max_length=8, choices=WalletTxnType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=120, blank=True)
    reference = models.CharField(max_length=255, blank=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Wallet transaction"
        verbose_name_plural = "Wallet transactions"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.txn_type} {self.amount} -> {self.balance_after}"


class GiftCardStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    REDEEMED = "redeemed", "Redeemed"
    DISABLED = "disabled", "Disabled"


class GiftCard(TenantOwnedModel):
    code = models.CharField(max_length=40)
    initial_balance = models.DecimalField(max_digits=12, decimal_places=2)
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=10, choices=GiftCardStatus.choices, default=GiftCardStatus.ACTIVE, db_index=True
    )

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Gift card"
        verbose_name_plural = "Gift cards"
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["store", "code"],
                condition=Q(is_deleted=False),
                name="uniq_gift_card_store_code",
            )
        ]

    def __str__(self) -> str:
        return self.code


class LoyaltyAccount(TenantOwnedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="loyalty_accounts"
    )
    points = models.PositiveIntegerField(default=0)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Loyalty account"
        verbose_name_plural = "Loyalty accounts"
        constraints = [
            models.UniqueConstraint(
                fields=["store", "user"],
                condition=Q(is_deleted=False),
                name="uniq_loyalty_per_store_user",
            )
        ]

    def __str__(self) -> str:
        return f"Loyalty({self.user_id}): {self.points}"


class LoyaltyTxnType(models.TextChoices):
    EARN = "earn", "Earn"
    REDEEM = "redeem", "Redeem"


class LoyaltyTransaction(TenantOwnedModel):
    account = models.ForeignKey(
        LoyaltyAccount, on_delete=models.CASCADE, related_name="transactions"
    )
    txn_type = models.CharField(max_length=8, choices=LoyaltyTxnType.choices)
    points = models.PositiveIntegerField()
    balance_after = models.PositiveIntegerField()
    reason = models.CharField(max_length=120, blank=True)
    reference = models.CharField(max_length=255, blank=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Loyalty transaction"
        verbose_name_plural = "Loyalty transactions"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.txn_type} {self.points} -> {self.balance_after}"
