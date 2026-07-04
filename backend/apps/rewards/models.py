"""Rewards domain models (store-scoped): wallet, gift cards, loyalty.

* ``Wallet`` / ``WalletTransaction``     — a buyer's store-credit balance + ledger.
* ``GiftCard``                           — a redeemable balance that tops up a wallet.
* ``LoyaltyAccount`` / ``LoyaltyTransaction`` — points earned on orders, redeemable
  into wallet credit.
* ``ReferralCode`` / ``Referral`` — a buyer's shareable code and the resulting
  referrals; both parties are credited to their wallet on the referee's first
  qualifying (confirmed) order.
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
    currency = models.CharField(max_length=3, default="EGP")

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


class ReferralCode(TenantOwnedModel):
    """A buyer's shareable referral code within a store (one per store+user)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="referral_codes"
    )
    code = models.CharField(max_length=20)
    uses_count = models.PositiveIntegerField(default=0, editable=False)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Referral code"
        verbose_name_plural = "Referral codes"
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["store", "user"],
                condition=Q(is_deleted=False),
                name="uniq_referral_code_store_user",
            ),
            models.UniqueConstraint(
                fields=["store", "code"],
                condition=Q(is_deleted=False),
                name="uniq_referral_code_store_code",
            ),
        ]

    def __str__(self) -> str:
        return self.code


class ReferralStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    REWARDED = "rewarded", "Rewarded"


class Referral(TenantOwnedModel):
    """A referral relationship: ``referrer`` invited ``referee`` via a code.

    Created (``pending``) when the referee applies a code, settled (``rewarded``)
    when the referee places their first qualifying confirmed order.
    """

    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="referrals_made"
    )
    referee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="referral_received"
    )
    code = models.CharField(max_length=20)
    status = models.CharField(
        max_length=10, choices=ReferralStatus.choices, default=ReferralStatus.PENDING, db_index=True
    )
    referrer_reward = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    referee_reward = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    order = models.ForeignKey(
        "orders.Order", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    rewarded_at = models.DateTimeField(null=True, blank=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Referral"
        verbose_name_plural = "Referrals"
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["store", "referee"],
                condition=Q(is_deleted=False),
                name="uniq_referral_store_referee",
            )
        ]
        indexes = [models.Index(fields=["store", "referrer"])]

    def __str__(self) -> str:
        return f"{self.referrer_id} -> {self.referee_id} ({self.status})"
