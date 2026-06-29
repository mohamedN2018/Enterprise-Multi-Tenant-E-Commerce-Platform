"""Payment application service.

Bridges the order lifecycle and the gateway layer: creating a payment initiates
it with the chosen gateway; capturing a payment settles it and — on success —
confirms the order, which commits the reserved stock (see ``CheckoutService``).
"""

from __future__ import annotations

from django.utils import timezone

from apps.core.exceptions import BusinessRuleError, ConflictError
from apps.core.services import BaseService, atomic
from apps.orders.models import OrderStatus
from apps.orders.services import CheckoutService
from apps.payments.gateways import get_gateway
from apps.payments.gateways.base import GatewayResult
from apps.payments.models import Payment, PaymentEvent, PaymentStatus

_CAPTURABLE = {PaymentStatus.PENDING, PaymentStatus.PROCESSING}


class PaymentService(BaseService):
    def __init__(self, checkout: CheckoutService | None = None) -> None:
        self.checkout = checkout or CheckoutService()

    @atomic
    def create_payment(self, *, store, user, order, gateway_code: str) -> Payment:
        if order.status != OrderStatus.PENDING:
            raise BusinessRuleError("This order is not awaiting payment.", code="order_not_payable")
        if order.payments.filter(status=PaymentStatus.CAPTURED).exists():
            raise ConflictError("This order has already been paid.", code="already_paid")

        gateway = get_gateway(gateway_code)  # validates code / availability
        payment = Payment.objects.create(
            store=store,
            order=order,
            user=user,
            gateway=gateway_code,
            amount=order.total,
            currency=order.currency,
            status=PaymentStatus.PENDING,
        )
        self._apply(payment, gateway.initiate(payment=payment), event="initiate")
        return payment

    @atomic
    def capture_payment(self, *, payment: Payment) -> Payment:
        if payment.status == PaymentStatus.CAPTURED:
            return payment
        if payment.status not in _CAPTURABLE:
            raise ConflictError("This payment can no longer be captured.", code="not_capturable")
        gateway = get_gateway(payment.gateway)
        self._apply(payment, gateway.capture(payment=payment), event="capture")

        if payment.status == PaymentStatus.CAPTURED and payment.order.status == OrderStatus.PENDING:
            self.checkout.confirm_order(order=payment.order)
        return payment

    def _apply(self, payment: Payment, result: GatewayResult, *, event: str) -> None:
        payment.status = result.status
        if result.transaction_id:
            payment.transaction_id = result.transaction_id
        if result.redirect_url:
            payment.redirect_url = result.redirect_url
        payment.error_message = result.error or ""
        if result.status == PaymentStatus.CAPTURED and payment.paid_at is None:
            payment.paid_at = timezone.now()
        payment.save()
        PaymentEvent.objects.create(
            store=payment.store,
            payment=payment,
            event_type=event,
            message=(result.error or result.status)[:255],
            data=result.raw,
        )
