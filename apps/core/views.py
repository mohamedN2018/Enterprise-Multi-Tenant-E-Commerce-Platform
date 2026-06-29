"""Operational endpoints for the core app."""

from __future__ import annotations

from django.db import connections
from django.db.utils import OperationalError
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.request import Request

from apps.core.responses import APIResponse


@extend_schema(
    summary="Health check",
    description="Liveness/readiness probe. Verifies database connectivity.",
    responses={200: None, 503: None},
    tags=["system"],
    auth=[],
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([])
def health_check(request: Request) -> APIResponse:
    """Return service health, including a database connectivity probe."""
    db_ok = True
    try:
        connections["default"].cursor()
    except OperationalError:
        db_ok = False

    if db_ok:
        return APIResponse.success(
            data={"status": "healthy", "database": "ok"},
            message="Service healthy",
        )
    return APIResponse.error(
        message="Service degraded",
        errors={"database": "unavailable"},
        error_code="service_unavailable",
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    )
