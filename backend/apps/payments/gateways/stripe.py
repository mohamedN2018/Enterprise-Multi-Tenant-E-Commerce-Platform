"""Stripe gateway adapter (stub).

Registered to demonstrate the pluggable interface. It deliberately performs no
external calls and raises a clear configuration error until real credentials and
the Stripe SDK are wired in — keeping the core dependency-free. Implement
``initiate``/``capture`` against the Stripe API to activate.
"""

from __future__ import annotations

from django.conf import settings

from apps.payments.exceptions import PaymentError
from apps.payments.gateways.base import GatewayResult, PaymentGateway
from apps.payments.gateways.registry import register


@register
class StripeGateway(PaymentGateway):
    code = "stripe"
    display_name = "Stripe"

    def _require_config(self) -> None:
        if not getattr(settings, "STRIPE_SECRET_KEY", ""):
            raise PaymentError(
                "Stripe is not configured. Set STRIPE_SECRET_KEY to enable it.",
                code="gateway_unconfigured",
            )

    def initiate(self, *, payment) -> GatewayResult:
        self._require_config()
        raise PaymentError(  # pragma: no cover - real integration pending
            "Stripe integration is not implemented yet.", code="not_implemented"
        )

    def capture(self, *, payment, **kwargs) -> GatewayResult:
        self._require_config()
        raise PaymentError(  # pragma: no cover - real integration pending
            "Stripe integration is not implemented yet.", code="not_implemented"
        )
