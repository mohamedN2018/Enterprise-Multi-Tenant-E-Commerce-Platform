"""Request helpers for the accounts app."""

from __future__ import annotations

from django.conf import settings


def get_client_ip(request) -> str | None:
    """The caller's IP, resistant to ``X-Forwarded-For`` spoofing.

    Each trusted reverse proxy *appends* the address it received the request
    from, so with ``TRUSTED_PROXY_COUNT`` proxies in front of the app the real
    client is the Nth entry counted from the right. Taking the left-most entry
    (the old behaviour) trusts a fully client-controlled value — an attacker
    could forge any IP into the audit log. Falls back to ``REMOTE_ADDR``.
    """
    trusted = getattr(settings, "TRUSTED_PROXY_COUNT", 1)
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded and trusted > 0:
        parts = [p.strip() for p in forwarded.split(",") if p.strip()]
        if len(parts) >= trusted:
            return parts[-trusted]
    return request.META.get("REMOTE_ADDR")


def _device_name_from_user_agent(user_agent: str) -> str:
    ua = user_agent.lower()
    os_name = next(
        (
            name
            for token, name in (
                ("windows", "Windows"),
                ("mac os", "macOS"),
                ("iphone", "iOS"),
                ("ipad", "iPadOS"),
                ("android", "Android"),
                ("linux", "Linux"),
            )
            if token in ua
        ),
        "Unknown OS",
    )
    browser = next(
        (
            name
            for token, name in (
                ("edg", "Edge"),
                ("chrome", "Chrome"),
                ("firefox", "Firefox"),
                ("safari", "Safari"),
            )
            if token in ua
        ),
        "Unknown browser",
    )
    return f"{browser} on {os_name}"


def extract_request_meta(request) -> dict:
    """Return ``{ip, user_agent, device_name}`` describing the caller."""
    user_agent = request.META.get("HTTP_USER_AGENT", "")[:1024]
    return {
        "ip": get_client_ip(request),
        "user_agent": user_agent,
        "device_name": _device_name_from_user_agent(user_agent),
    }
