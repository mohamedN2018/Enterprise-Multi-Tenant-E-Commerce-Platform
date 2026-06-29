"""Payment gateway interface (Strategy pattern).

Each concrete gateway implements ``initiate`` and ``capture`` and returns a
``GatewayResult``. Gateways are pluggable modules that self-register via
:func:`apps.payments.gateways.registry.register`; the rest of the system only
talks to this interface, never to a specific provider.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from apps.payments.exceptions import PaymentError

if TYPE_CHECKING:  # pragma: no cover
    from apps.payments.models import Payment


@dataclass
class GatewayResult:
    status: str  # a PaymentStatus value
    success: bool = True
    transaction_id: str = ""
    redirect_url: str = ""
    error: str = ""
    raw: dict = field(default_factory=dict)


class PaymentGateway(ABC):
    code: str = ""
    display_name: str = ""

    @abstractmethod
    def initiate(self, *, payment: Payment) -> GatewayResult:
        """Begin a payment (authorize / create a redirect / client secret)."""

    @abstractmethod
    def capture(self, *, payment: Payment, **kwargs) -> GatewayResult:
        """Capture/settle a previously initiated payment."""

    def refund(self, *, payment: Payment, amount) -> GatewayResult:
        raise PaymentError(
            "Refunds are not supported by this gateway yet.", code="refund_unsupported"
        )
