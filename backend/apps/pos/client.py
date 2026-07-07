"""HTTP client for an external POS supplier (e.g. "q-shop POS").

Server-to-server, so no CORS concerns. Every request carries ``x-api-key`` plus
optional ``x-store-name`` / ``x-store-url`` so the cashier knows who connected.
Uses the stdlib ``urllib`` (no extra dependency). Transient 5xx / network errors
are retried a few times; a 401 is surfaced as an invalid-key error.
"""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request

from apps.core.exceptions import DomainError


class PosAuthError(DomainError):
    status_code = 400
    code = "pos_invalid_key"
    message = "The cashier system rejected the API key."


class PosUnavailableError(DomainError):
    status_code = 502
    code = "pos_unavailable"
    message = "Couldn't reach the cashier system. Please try again shortly."


class PosSupplierClient:
    def __init__(self, *, api_url: str, api_key: str, store_name: str = "", store_url: str = "", timeout: int = 10):
        self.base = (api_url or "").rstrip("/")
        self.api_key = api_key
        self.store_name = store_name
        self.store_url = store_url
        self.timeout = timeout

    def _headers(self) -> dict:
        headers = {"x-api-key": self.api_key, "Accept": "application/json"}
        if self.store_name:
            headers["x-store-name"] = self.store_name
        if self.store_url:
            headers["x-store-url"] = self.store_url
        return headers

    def _get(self, path: str, *, retries: int = 2):
        request = urllib.request.Request(
            f"{self.base}{path}", headers=self._headers(), method="GET"
        )
        attempt = 0
        while True:
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as resp:
                    return json.loads(resp.read().decode("utf-8") or "null")
            except urllib.error.HTTPError as exc:
                if exc.code == 401:
                    raise PosAuthError() from exc
                if 500 <= exc.code < 600 and attempt < retries:
                    attempt += 1
                    continue
                raise PosUnavailableError(f"The cashier system returned HTTP {exc.code}.") from exc
            except (urllib.error.URLError, socket.timeout, OSError) as exc:
                if attempt < retries:
                    attempt += 1
                    continue
                raise PosUnavailableError(str(exc)) from exc

    def verify(self) -> dict:
        """GET /integration/store — 200 confirms the key; returns store summary."""
        return self._get("/integration/store") or {}

    def fetch_products(self) -> list:
        """GET /integration/products — the supplier's catalog as a list."""
        data = self._get("/integration/products")
        if isinstance(data, dict):  # tolerate {results:[...]} or {products:[...]}
            data = data.get("products") or data.get("results") or []
        return data or []
