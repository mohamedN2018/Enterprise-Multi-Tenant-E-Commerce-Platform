"""Bundled payment gateways.

Importing this package registers every gateway module (each uses ``@register``).
Add new providers by creating a module here and importing it below.
"""

from apps.payments.gateways import manual, stripe  # noqa: F401  (registration side-effects)
from apps.payments.gateways.registry import (
    available_gateways,
    get_gateway,
    register,
)

__all__ = ["available_gateways", "get_gateway", "register"]
