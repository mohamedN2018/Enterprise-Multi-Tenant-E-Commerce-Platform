"""Request-ID correlation tests (B3)."""

from __future__ import annotations

import logging

import pytest
from django.test import Client

from apps.core.observability import REQUEST_ID_HEADER, RequestIDFilter, get_request_id

pytestmark = pytest.mark.django_db


def test_response_carries_a_request_id():
    response = Client().get("/health/")
    assert response.status_code == 200
    assert response.headers.get(REQUEST_ID_HEADER)  # generated when absent


def test_client_request_id_is_echoed():
    response = Client().get("/health/", HTTP_X_REQUEST_ID="abc-123")
    assert response.headers.get(REQUEST_ID_HEADER) == "abc-123"


def test_logging_filter_tags_records():
    record = logging.LogRecord("x", logging.INFO, __file__, 1, "msg", None, None)
    assert RequestIDFilter().filter(record) is True
    assert hasattr(record, "request_id")


def test_request_id_defaults_outside_request():
    # No active request -> sentinel default.
    assert get_request_id() == "-"
