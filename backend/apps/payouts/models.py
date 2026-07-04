"""Seller payouts & commissions (store-scoped via ``TenantOwnedModel``).

In this marketplace each store is a seller. On every confirmed order the platform
takes a commission and the remainder (net) is credited to the store's
``SellerAccount``; the seller can later request a ``Payout`` of their balance.

* ``SellerAccount`` — the store's running balance + its commission rate.
* ``LedgerEntry``   — append-only record of every earning / payout / adjustment.
* ``Payout``        — a withdrawal request (pending -> paid / failed).
"""

from __future__ import annotations

from decimal import Decimal

from django.db import models

from apps.core.models import TenantOwnedModel


class SellerAccount(TenantOwnedModel):
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="EGP")
    commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )  # platform commission percentage

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Seller account"
        verbose_name_plural = "Seller accounts"
        constraints = [
            models.UniqueConstraint(
                fields=["store"],
                condition=models.Q(is_deleted=False),
                name="uniq_seller_account_store",
            )
        ]

    def __str__(self) -> str:
        return f"SellerAccount({self.store_id}): {self.balance} {self.currency}"


class LedgerEntryType(models.TextChoices):
    EARNING = "earning", "Earning"
    PAYOUT = "payout", "Payout"
    ADJUSTMENT = "adjustment", "Adjustment"


class LedgerEntry(TenantOwnedModel):
    account = models.ForeignKey(SellerAccount, on_delete=models.CASCADE, related_name="entries")
    entry_type = models.CharField(max_length=12, choices=LedgerEntryType.choices, db_index=True)
    order = models.ForeignKey(
        "orders.Order", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    gross_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    commission_amount = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00")
    )
    # Signed: positive credits the seller (earning), negative debits (payout).
    net_amount = models.DecimalField(max_digits=14, decimal_places=2)
    balance_after = models.DecimalField(max_digits=14, decimal_places=2)
    reference = models.CharField(max_length=255, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Ledger entry"
        verbose_name_plural = "Ledger entries"
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["store", "entry_type"])]

    def __str__(self) -> str:
        return f"{self.entry_type} {self.net_amount} -> {self.balance_after}"


class PayoutStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    FAILED = "failed", "Failed"


class Payout(TenantOwnedModel):
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(
        max_length=10, choices=PayoutStatus.choices, default=PayoutStatus.PENDING, db_index=True
    )
    reference = models.CharField(max_length=255, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Payout"
        verbose_name_plural = "Payouts"
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["store", "status"])]

    def __str__(self) -> str:
        return f"Payout {self.amount} [{self.status}]"
