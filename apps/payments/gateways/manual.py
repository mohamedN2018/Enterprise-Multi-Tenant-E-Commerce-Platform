"""Manual gateway: cash on delivery / bank transfer / staff-marked payments.

Fully functional and dependency-free. ``initiate`` marks the payment as awaiting
collection; ``capture`` settles it (e.g. cash received / transfer confirmed).
"""

from __future__ import annotations

from apps.payments.gateways.base import GatewayResult, PaymentGateway
from apps.payments.gateways.registry import register
from apps.payments.models import PaymentStatus


@register
class ManualGateway(PaymentGateway):
    code = "manual"
    display_name = "Manual / Cash"

    def initiate(self, *, payment) -> GatewayResult:
        return GatewayResult(
            status=PaymentStatus.PROCESSING,
            raw={"note": "Awaiting manual collection."},
        )

    def capture(self, *, payment, **kwargs) -> GatewayResult:
        return GatewayResult(
            status=PaymentStatus.CAPTURED,
            transaction_id=f"manual-{payment.id}",
            raw={"note": "Marked as collected."},
        )
