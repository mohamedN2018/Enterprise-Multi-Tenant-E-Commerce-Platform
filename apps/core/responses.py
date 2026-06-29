"""Consistent success envelope: renderer + helper.

Every JSON response shares one shape::

    {"success": bool, "message": str, "data": ..., "errors": ..., "meta"?: ...}

* :class:`EnvelopeJSONRenderer` wraps any view payload that is not already
  enveloped (errors come pre-enveloped from the exception handler; paginated
  lists from the pagination class).
* :class:`APIResponse` is for views that want to set message/meta explicitly.
"""

from __future__ import annotations

from typing import Any

from rest_framework import status as http_status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

_DEFAULT_MESSAGES = {
    http_status.HTTP_200_OK: "OK",
    http_status.HTTP_201_CREATED: "Created",
    http_status.HTTP_202_ACCEPTED: "Accepted",
}


def _is_enveloped(data: Any) -> bool:
    return isinstance(data, dict) and "success" in data


class EnvelopeJSONRenderer(JSONRenderer):
    """Normalise un-enveloped success payloads into the standard envelope."""

    def render(self, data, accepted_media_type=None, renderer_context=None):
        renderer_context = renderer_context or {}
        response = renderer_context.get("response")
        status_code = getattr(response, "status_code", http_status.HTTP_200_OK)

        if not _is_enveloped(data):
            data = {
                "success": http_status.is_success(status_code),
                "message": _DEFAULT_MESSAGES.get(status_code, "OK"),
                "data": data,
                "errors": None,
            }
        return super().render(data, accepted_media_type, renderer_context)


class APIResponse:
    """Factory for explicit, well-formed envelope responses in views."""

    @staticmethod
    def success(
        data: Any = None,
        *,
        message: str = "OK",
        status_code: int = http_status.HTTP_200_OK,
        meta: dict | None = None,
    ) -> Response:
        body: dict[str, Any] = {
            "success": True,
            "message": message,
            "data": data,
            "errors": None,
        }
        if meta is not None:
            body["meta"] = meta
        return Response(body, status=status_code)

    @staticmethod
    def error(
        message: str,
        *,
        errors: Any = None,
        error_code: str = "error",
        status_code: int = http_status.HTTP_400_BAD_REQUEST,
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
