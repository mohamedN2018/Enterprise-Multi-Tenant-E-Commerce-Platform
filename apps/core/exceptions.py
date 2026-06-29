"""Domain exception hierarchy + DRF exception handler.

Service/domain code raises the typed exceptions below; the handler converts any
exception (domain, DRF, or Django) into the project's consistent error envelope:

    {
      "success": false,
      "message": "...",
      "data": null,
      "errors": {...} | [...] | null,
      "error_code": "..."
    }
"""
from __future__ import annotations

from typing import Any, Optional

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


# --- Domain exceptions -----------------------------------------------------
class DomainError(Exception):
    """Base class for expected, business-level errors."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "error"
    message: str = "A domain error occurred."

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        errors: Any = None,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
    ) -> None:
        self.message = message or self.message
        self.errors = errors
        self.code = code or self.code
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.message)


class ValidationError(DomainError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "validation_error"
    message = "Validation failed."


class AuthenticationError(DomainError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "authentication_failed"
    message = "Authentication failed."


class PermissionDeniedError(DomainError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "permission_denied"
    message = "You do not have permission to perform this action."


class NotFoundError(DomainError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"
    message = "The requested resource was not found."


class ConflictError(DomainError):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"
    message = "The request conflicts with the current state of the resource."


class BusinessRuleError(DomainError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    code = "business_rule_violation"
    message = "The operation violates a business rule."


# --- Handler ---------------------------------------------------------------
def _envelope(
    *, message: str, errors: Any, error_code: str, status_code: int
) -> Response:
    return Response(
        {
            "success": False,
            "message": message,
            "data": None,
            "errors": errors,
            "error_code": error_code,
        },
        status=status_code,
    )


def _extract(response: Response, exc: Exception) -> tuple[str, Any, str]:
    data = response.data
    error_code = getattr(exc, "default_code", None) or "error"

    if isinstance(data, dict) and set(data.keys()) == {"detail"}:
        return str(data["detail"]), None, error_code
    if isinstance(data, dict):
        return "Validation failed.", data, error_code
    if isinstance(data, list):
        return "The request could not be processed.", data, error_code
    return str(data), None, error_code


def custom_exception_handler(exc: Exception, context: dict) -> Optional[Response]:
    # 1) Our own domain errors map directly to the envelope.
    if isinstance(exc, DomainError):
        return _envelope(
            message=exc.message,
            errors=exc.errors,
            error_code=exc.code,
            status_code=exc.status_code,
        )

    # 2) Normalise common Django exceptions into DRF equivalents.
    if isinstance(exc, DjangoValidationError):
        exc = DRFValidationError(detail=list(exc.messages))
    elif isinstance(exc, DjangoPermissionDenied):
        return _envelope(
            message="You do not have permission to perform this action.",
            errors=None,
            error_code="permission_denied",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    elif isinstance(exc, Http404):
        return _envelope(
            message="The requested resource was not found.",
            errors=None,
            error_code="not_found",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # 3) Delegate to DRF for the rest, then re-wrap into the envelope.
    response = drf_exception_handler(exc, context)
    if response is None:
        return None  # Unexpected error -> Django's 500 handling / middleware.

    message, errors, error_code = _extract(response, exc)
    response.data = {
        "success": False,
        "message": message,
        "data": None,
        "errors": errors,
        "error_code": error_code,
    }
    return response
