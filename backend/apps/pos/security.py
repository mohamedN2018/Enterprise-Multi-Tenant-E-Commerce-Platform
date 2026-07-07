"""SSRF protection for server-side fetches to a seller-supplied URL.

``connect`` and image import make the platform fetch an arbitrary URL the seller
typed. Without checks that is a Server-Side Request Forgery vector: a URL could
point at ``localhost``, cloud metadata (``169.254.169.254``) or the internal
network. We require http(s) and reject any host that resolves to a private,
loopback, link-local or otherwise non-public address.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from django.conf import settings

from apps.core.exceptions import ValidationError


def _is_blocked_ip(ip: str) -> bool:
    addr = ipaddress.ip_address(ip)
    return (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_reserved
        or addr.is_multicast
        or addr.is_unspecified
    )


def is_public_url(url: str) -> bool:
    """True if ``url`` is http(s) and every resolved address is public."""
    if getattr(settings, "POS_ALLOW_UNSAFE_URLS", False):
        return True
    parsed = urlparse(url or "")
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return False
    host = parsed.hostname.lower()
    if host == "localhost" or host.endswith(".localhost"):
        return False
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        return False
    return bool(infos) and not any(_is_blocked_ip(info[4][0]) for info in infos)


def assert_public_url(url: str) -> None:
    """Raise if ``url`` is not a safe, public http(s) endpoint."""
    if not is_public_url(url):
        raise ValidationError(
            "The API URL must be a public http(s) address (private/internal "
            "addresses are not allowed).",
            code="blocked_url",
        )
