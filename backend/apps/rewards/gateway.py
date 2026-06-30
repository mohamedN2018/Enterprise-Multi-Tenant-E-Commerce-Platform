"""Store-credit (wallet) payment gateway.

Registers with the payments registry so an order can be paid from the buyer's
wallet. Capture debits the wallet for the payment amount; an insufficient balance
raises and rolls the capture back (the order stays pending).
"""

from __future__ import annotations

from apps.payments.gateways.base import GatewayResult, PaymentGateway
from apps.payments.gateways.registry import register
from apps.payments.models import PaymentStatus


@register
class StoreCreditGateway(PaymentGateway):
    code = "store_credit"
    display_name = "Store credit (wallet)"

    def initiate(self, *, payment) -> GatewayResult:
        return GatewayResult(status=PaymentStatus.PROCESSING)

    def capture(self, *, payment, **kwargs) -> GatewayResult:
        from apps.rewards.services import WalletService

        WalletService().debit(
            store=payment.store,
            user=payment.user,
            amount=payment.amount,
            reason="order_payment",
            reference=f"order:{payment.order_id}",
        )
        return GatewayResult(status=PaymentStatus.CAPTURED, transaction_id=f"wallet-{payment.id}")
