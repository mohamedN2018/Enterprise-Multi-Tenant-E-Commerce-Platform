"""Gateway registry + lookup.

Gateways register themselves with ``@register``. ``get_gateway`` resolves a code
to an instance, enforcing the per-deployment allow-list
(``settings.PAYMENT_ENABLED_GATEWAYS``).
"""

from __future__ import annotations

from django.conf import settings

from apps.payments.exceptions import PaymentError
from apps.payments.gateways.base import PaymentGateway

_REGISTRY: dict[str, type[PaymentGateway]] = {}


def register(cls: type[PaymentGateway]) -> type[PaymentGateway]:
    if not getattr(cls, "code", ""):
        raise ValueError(f"Gateway {cls.__name__} must define a non-empty `code`.")
    _REGISTRY[cls.code] = cls
    return cls


def _enabled_codes() -> list[str]:
    enabled = getattr(settings, "PAYMENT_ENABLED_GATEWAYS", ["manual"])
    return [code for code in enabled if code in _REGISTRY]


def available_gateways() -> list[dict]:
    return [
        {"code": code, "display_name": _REGISTRY[code].display_name} for code in _enabled_codes()
    ]


def get_gateway(code: str) -> PaymentGateway:
    if code not in _enabled_codes():
        raise PaymentError(
            f"Payment gateway '{code}' is not available.", code="gateway_unavailable"
        )
    return _REGISTRY[code]()
