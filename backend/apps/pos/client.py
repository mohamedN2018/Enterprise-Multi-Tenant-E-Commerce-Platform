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
from urllib.parse import quote

from apps.core.exceptions import DomainError
from apps.pos import security

# POS providers are often fronted by Cloudflare, which blocks the default
# "Python-urllib/x" agent as a bot. Present a normal browser UA so our
# server-to-server calls aren't challenged before they reach the POS app.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)


class PosAuthError(DomainError):
    status_code = 400
    code = "pos_invalid_key"
    message = "The cashier system rejected the API key."


class PosUnavailableError(DomainError):
    status_code = 502
    code = "pos_unavailable"
    message = "Couldn't reach the cashier system. Please try again shortly."


class PosOutOfStockError(DomainError):
    status_code = 409
    code = "pos_out_of_stock"
    message = "Some items are no longer in stock."

    def __init__(self, *, items=None):
        super().__init__(errors={"out_of_stock": items or []})
        self.items = items or []


class PosSupplierClient:
    def __init__(self, *, api_url: str, api_key: str, store_name: str = "", store_url: str = "", timeout: int = 8):
        self.base = (api_url or "").rstrip("/")
        self.api_key = api_key
        self.store_name = store_name
        self.store_url = store_url
        self.timeout = timeout

    def _headers(self) -> dict:
        headers = {
            "x-api-key": self.api_key,
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }
        # HTTP header values must be latin-1. A store name in Arabic (or any
        # non-ASCII) would crash urllib before the request is sent, so
        # percent-encode these optional identity headers — always ASCII-safe.
        # The cashier can decodeURIComponent() them to show the original text.
        if self.store_name:
            headers["x-store-name"] = quote(self.store_name, safe="")
        if self.store_url:
            headers["x-store-url"] = quote(self.store_url, safe=":/?=&")
        return headers

    def _request(self, method: str, path: str, *, data=None, retries: int = 1):
        # Keep the total blocking budget (attempts × timeout) well under the
        # server's worker timeout so a slow/unreachable POS fails fast with a
        # clear error rather than hanging into a gateway 500.
        headers = self._headers()
        body_bytes = None
        if data is not None:
            body_bytes = json.dumps(data).encode()
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            f"{self.base}{path}", data=body_bytes, headers=headers, method=method
        )
        attempt = 0
        while True:
            try:
                # SSRF-hardened: validates the target + every redirect hop is public.
                with security.open_public_url(request, timeout=self.timeout) as resp:
                    body = resp.read().decode("utf-8", errors="replace")
            except urllib.error.HTTPError as exc:
                if exc.code == 401:
                    raise PosAuthError() from exc
                if exc.code == 409:  # cashier: insufficient stock
                    try:
                        detail = json.loads(exc.read().decode("utf-8", "replace") or "{}")
                    except (ValueError, OSError):
                        detail = {}
                    raise PosOutOfStockError(items=detail.get("out_of_stock") or []) from exc
                if 500 <= exc.code < 600 and attempt < retries:
                    attempt += 1
                    continue
                raise PosUnavailableError(f"The cashier system returned HTTP {exc.code}.") from exc
            except (urllib.error.URLError, socket.timeout, OSError) as exc:
                if attempt < retries:
                    attempt += 1
                    continue
                raise PosUnavailableError(str(exc)) from exc
            # A 200 with a non-JSON body (e.g. an HTML error page) is a bad response,
            # not a server error on our side — surface it as unavailable, never a 500.
            try:
                return json.loads(body or "null")
            except ValueError as exc:
                raise PosUnavailableError(
                    "The cashier system returned an unexpected (non-JSON) response."
                ) from exc

    def _get(self, path: str, *, retries: int = 1):
        return self._request("GET", path, retries=retries)

    def verify(self) -> dict:
        """GET /integration/store — 200 confirms the key; returns store summary."""
        data = self._get("/integration/store")
        return data if isinstance(data, dict) else {}

    def fetch_products(self) -> list:
        """GET /integration/products — the supplier's catalog as a list."""
        data = self._get("/integration/products")
        if isinstance(data, dict):  # tolerate {results:[...]} or {products:[...]}
            data = data.get("products") or data.get("results") or []
        return data if isinstance(data, list) else []

    def push_order(self, payload: dict) -> dict:
        """POST /integration/orders — push a placed order to the cashier's log."""
        data = self._request("POST", "/integration/orders", data=payload)
        return data if isinstance(data, dict) else {}
