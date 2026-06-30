"""Payment domain exceptions (handled by the global DRF exception handler)."""

from __future__ import annotations

from rest_framework import status

from apps.core.exceptions import DomainError


class PaymentError(DomainError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "payment_error"
    message = "The payment could not be processed."
