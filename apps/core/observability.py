"""Request-ID correlation for logs and responses.

Every request gets an ``X-Request-ID`` (honoured from the client / upstream proxy
if present, else generated). It is stored in a ContextVar so log records made
anywhere during the request can be tagged with it (via :class:`RequestIDFilter`),
and echoed back on the response — giving end-to-end traceability across the API,
Celery logs and the frontend.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from contextvars import ContextVar

from django.http import HttpRequest, HttpResponse

_request_id: ContextVar[str] = ContextVar("request_id", default="-")

REQUEST_ID_HEADER = "X-Request-ID"
_META_KEY = "HTTP_X_REQUEST_ID"


def get_request_id() -> str:
    return _request_id.get()


class RequestIDFilter(logging.Filter):
    """Inject ``request_id`` into every log record for the active request."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


class RequestIDMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = request.META.get(_META_KEY) or uuid.uuid4().hex
        token = _request_id.set(request_id)
        request.request_id = request_id  # type: ignore[attr-defined]
        try:
            response = self.get_response(request)
            response[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            _request_id.reset(token)
