"""Rewards API views (buyer wallet/loyalty/redeem; staff gift-card issuing)."""

from __future__ import annotations

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.core.mixins import BaseAPIView, BaseGenericAPIView
from apps.core.responses import APIResponse
from apps.rewards.models import GiftCard
from apps.rewards.serializers import (
    GiftCardSerializer,
    IssueGiftCardSerializer,
    RedeemGiftCardSerializer,
    RedeemPointsSerializer,
    WalletTransactionSerializer,
)
from apps.rewards.services import GiftCardService, LoyaltyService, WalletService
from apps.stores.context import RequireStoreMixin, StoreContextMixin


# --- Buyer: wallet ---------------------------------------------------------
class WalletView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        service = WalletService()
        balance = service.balance(store=self.store, user=request.user)
        transactions = service.history(store=self.store, user=request.user)[:20]
        return APIResponse.success(
            data={
                "balance": str(balance),
                "currency": self.store.currency,
                "transactions": WalletTransactionSerializer(transactions, many=True).data,
            }
        )


# --- Buyer: gift cards -----------------------------------------------------
class GiftCardRedeemView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RedeemGiftCardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = GiftCardService().redeem(
            store=self.store, user=request.user, code=serializer.validated_data["code"]
        )
        balance = WalletService().balance(store=self.store, user=request.user)
        return APIResponse.success(
            data={"redeemed": str(amount), "wallet_balance": str(balance)},
            message="Gift card redeemed to your wallet.",
        )


# --- Buyer: loyalty --------------------------------------------------------
class LoyaltyView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        points = LoyaltyService().balance(store=self.store, user=request.user)
        return APIResponse.success(data={"points": points})


class LoyaltyRedeemView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RedeemPointsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = LoyaltyService().redeem(
            store=self.store, user=request.user, points=serializer.validated_data["points"]
        )
        return APIResponse.success(
            data={
                "points_redeemed": result["points_redeemed"],
                "wallet_credit": str(result["wallet_credit"]),
                "loyalty_balance": result["loyalty_balance"],
            },
            message="Points redeemed to wallet credit.",
        )


# --- Staff: gift cards -----------------------------------------------------
class GiftCardListCreateView(StoreContextMixin, BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GiftCardSerializer
    filterset_fields = ("status",)

    def get_queryset(self):
        return GiftCard.objects.all()

    def post(self, request, *args, **kwargs):
        self.require_write()
        serializer = IssueGiftCardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        card = GiftCardService().issue(
            store=self.store,
            amount=serializer.validated_data["amount"],
            code=serializer.validated_data.get("code") or None,
        )
        return APIResponse.success(
            GiftCardSerializer(card).data, message="Gift card issued.", status_code=201
        )
