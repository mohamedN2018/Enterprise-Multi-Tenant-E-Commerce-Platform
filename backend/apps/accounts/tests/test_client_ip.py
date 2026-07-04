"""get_client_ip: resistant to X-Forwarded-For spoofing."""

from __future__ import annotations

from django.test import override_settings

from apps.accounts.utils import get_client_ip


class _Req:
    def __init__(self, **meta):
        self.META = meta


@override_settings(TRUSTED_PROXY_COUNT=1)
def test_single_proxy_uses_rightmost_entry():
    # nginx appends the real client; a client-forged left entry is ignored.
    req = _Req(HTTP_X_FORWARDED_FOR="1.2.3.4, 203.0.113.9", REMOTE_ADDR="10.0.0.2")
    assert get_client_ip(req) == "203.0.113.9"


@override_settings(TRUSTED_PROXY_COUNT=2)
def test_two_proxies_counts_from_right():
    req = _Req(
        HTTP_X_FORWARDED_FOR="1.2.3.4, 203.0.113.9, 10.0.0.3", REMOTE_ADDR="10.0.0.2"
    )
    assert get_client_ip(req) == "203.0.113.9"


@override_settings(TRUSTED_PROXY_COUNT=1)
def test_falls_back_to_remote_addr_without_xff():
    assert get_client_ip(_Req(REMOTE_ADDR="198.51.100.7")) == "198.51.100.7"


@override_settings(TRUSTED_PROXY_COUNT=0)
def test_no_trusted_proxy_ignores_xff():
    req = _Req(HTTP_X_FORWARDED_FOR="1.2.3.4", REMOTE_ADDR="198.51.100.7")
    assert get_client_ip(req) == "198.51.100.7"
