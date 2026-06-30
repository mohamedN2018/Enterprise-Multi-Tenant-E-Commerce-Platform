"""Returns (RMA) application service.

Lifecycle: requested -> approved -> refunded (or rejected/cancelled). On refund
the returned items are restocked into inventory and the buyer is credited to
their wallet, all inside one transaction.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Sum
from django.utils import timezone

from apps.core.exceptions import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from apps.core.services import BaseService, atomic
from apps.orders.models import Order, OrderStatus
from apps.returns.models import (
    ACTIVE_RETURN_STATUSES,
    ReturnItem,
    ReturnRequest,
    ReturnResolution,
    ReturnStatus,
)

_CENTS = Decimal("0.01")


def _money(value) -> Decimal:
    return Decimal(value).quantize(_CENTS, rounding=ROUND_HALF_UP)


class ReturnService(BaseService):
    # --- Lookups ---
    def get_for_user(self, *, user, return_id) -> ReturnRequest:
        rma = ReturnRequest.objects.filter(id=return_id, user=user).first()
        if rma is None:
            raise NotFoundError("Return request not found.")
        return rma

    def get_for_store(self, *, return_id) -> ReturnRequest:
        rma = ReturnRequest.objects.filter(id=return_id).first()
        if rma is None:
            raise NotFoundError("Return request not found.")
        return rma

    def _returned_quantity(self, order_item) -> int:
        return (
            ReturnItem.objects.filter(
                order_item=order_item, return_request__status__in=ACTIVE_RETURN_STATUSES
            ).aggregate(total=Sum("quantity"))["total"]
            or 0
        )

    # --- Buyer actions ---
    @atomic
    def create_return(
        self,
        *,
        store,
        user,
        order_id,
        items: list,
        reason: str = "",
        resolution: str = ReturnResolution.REFUND,
    ) -> ReturnRequest:
        order = Order.objects.filter(id=order_id, user=user).prefetch_related("items").first()
        if order is None:
            raise NotFoundError("Order not found.")
        if order.status != OrderStatus.CONFIRMED:
            raise BusinessRuleError(
                "Only confirmed orders can be returned.", code="order_not_returnable"
            )
        if not items:
            raise ValidationError("Select at least one item to return.", code="no_items")

        rma = ReturnRequest.objects.create(
            store=store,
            order=order,
            user=user,
            reason=reason,
            resolution=resolution,
            status=ReturnStatus.REQUESTED,
        )
        order_items = {str(oi.id): oi for oi in order.items.all()}
        total = Decimal("0.00")
        for entry in items:
            order_item = order_items.get(str(entry["order_item_id"]))
            if order_item is None:
                raise ValidationError(
                    "Order item does not belong to this order.", code="invalid_order_item"
                )
            quantity = entry["quantity"]
            available = order_item.quantity - self._returned_quantity(order_item)
            if quantity <= 0 or quantity > available:
                raise BusinessRuleError(
                    f"Cannot return {quantity} of {order_item.sku}; {available} available.",
                    code="invalid_return_quantity",
                )
            ReturnItem.objects.create(
                store=store,
                return_request=rma,
                order_item=order_item,
                variant=order_item.variant,
                quantity=quantity,
                reason=entry.get("reason", ""),
            )
            total += order_item.unit_price * quantity

        rma.refund_amount = _money(total)
        rma.save(update_fields=["refund_amount", "updated_at"])
        return rma

    @atomic
    def cancel(self, *, rma: ReturnRequest) -> ReturnRequest:
        if rma.status != ReturnStatus.REQUESTED:
            raise ConflictError("Only a requested return can be cancelled.", code="not_cancellable")
        rma.status = ReturnStatus.CANCELLED
        rma.save(update_fields=["status", "updated_at"])
        return rma

    # --- Staff actions ---
    @atomic
    def approve(self, *, rma: ReturnRequest) -> ReturnRequest:
        if rma.status != ReturnStatus.REQUESTED:
            raise ConflictError("Only a requested return can be approved.", code="not_approvable")
        rma.status = ReturnStatus.APPROVED
        rma.save(update_fields=["status", "updated_at"])
        return rma

    @atomic
    def reject(self, *, rma: ReturnRequest, reason: str = "") -> ReturnRequest:
        if rma.status != ReturnStatus.REQUESTED:
            raise ConflictError("Only a requested return can be rejected.", code="not_rejectable")
        rma.status = ReturnStatus.REJECTED
        if reason:
            rma.reason = f"{rma.reason}\nRejected: {reason}".strip()
        rma.save(update_fields=["status", "reason", "updated_at"])
        return rma

    @atomic
    def refund(self, *, rma: ReturnRequest) -> ReturnRequest:
        if rma.status != ReturnStatus.APPROVED:
            raise ConflictError(
                "The return must be approved before it can be refunded.", code="not_refundable"
            )
        self._restock(rma)
        if rma.refund_amount > 0:
            rma.refund_reference = self._issue_refund(rma)
        rma.status = ReturnStatus.REFUNDED
        rma.processed_at = timezone.now()
        rma.save(update_fields=["status", "refund_reference", "processed_at", "updated_at"])
        return rma

    def _issue_refund(self, rma: ReturnRequest) -> str:
        """Refund to the original gateway when possible, else to store credit.

        A buyer who chose ``STORE_CREDIT`` is always credited to their wallet.
        Otherwise the original captured payment's gateway is tried first; if there
        is none, or it cannot refund, the amount falls back to wallet credit.
        """
        if rma.resolution != ReturnResolution.STORE_CREDIT:
            reference = self._gateway_refund(rma)
            if reference is not None:
                return reference
        self._wallet_refund(rma)
        return "wallet"

    def _gateway_refund(self, rma: ReturnRequest) -> str | None:
        from apps.payments.exceptions import PaymentError
        from apps.payments.models import Payment, PaymentStatus
        from apps.payments.services import PaymentService

        payment = (
            Payment.objects.filter(store=rma.store, order=rma.order, status=PaymentStatus.CAPTURED)
            .order_by("-created_at")
            .first()
        )
        if payment is None:
            return None
        try:
            PaymentService().refund_payment(payment=payment, amount=rma.refund_amount)
        except PaymentError:
            return None  # gateway can't refund -> caller falls back to store credit
        return f"gateway:{payment.gateway}"

    def _wallet_refund(self, rma: ReturnRequest) -> None:
        from apps.rewards.services import WalletService

        WalletService().credit(
            store=rma.store,
            user=rma.user,
            amount=rma.refund_amount,
            reason="refund",
            reference=f"return:{rma.id}",
        )

    def _restock(self, rma: ReturnRequest) -> None:
        from apps.catalog.models import ProductType
        from apps.inventory.models import Warehouse
        from apps.inventory.services import InventoryService

        warehouse = (
            Warehouse.objects.filter(store=rma.store, is_active=True).order_by("created_at").first()
        )
        if warehouse is None:
            return  # nowhere to restock (e.g. digital-only store)
        inventory = InventoryService()
        for item in rma.items.select_related("variant__product"):
            if item.variant.product.product_type == ProductType.DIGITAL:
                continue
            inventory.receive(
                store=rma.store,
                variant=item.variant,
                warehouse=warehouse,
                quantity=item.quantity,
                reference=f"return:{rma.id}",
                note="RMA restock",
            )
