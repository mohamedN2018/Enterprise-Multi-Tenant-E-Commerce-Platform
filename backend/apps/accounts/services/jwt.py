"""Low-level JWT mechanics built on SimpleJWT + the token_blacklist app.

Kept separate from device/session bookkeeping so the higher-level services can
compose token issuance, rotation and revocation without duplicating SimpleJWT
details.
"""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken


def issue_for_user(user, *, remember_me: bool = False) -> dict:
    """Create an access/refresh pair. Records an OutstandingToken (blacklist app)."""
    refresh = RefreshToken.for_user(user)
    if remember_me:
        days = settings.AUTH_SETTINGS["REMEMBER_ME_REFRESH_DAYS"]
        refresh.set_exp(lifetime=timedelta(days=days))
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "jti": str(refresh["jti"]),
    }


def rotate(raw_refresh: str) -> tuple[str, str]:
    """Validate & blacklist an existing refresh token.

    Returns ``(old_jti, user_id)``. Raises ``TokenError`` if the token is
    invalid, expired or already blacklisted.
    """
    old = RefreshToken(raw_refresh)
    old_jti = str(old["jti"])
    user_id = str(old[settings.SIMPLE_JWT["USER_ID_CLAIM"]])
    old.blacklist()
    return old_jti, user_id


def blacklist_raw(raw_refresh: str) -> str:
    """Blacklist a refresh token by value. Returns its jti. Raises ``TokenError``."""
    token = RefreshToken(raw_refresh)
    jti = str(token["jti"])
    token.blacklist()
    return jti


def blacklist_jti(jti: str) -> None:
    """Blacklist whatever outstanding token currently carries ``jti`` (idempotent)."""
    outstanding: OutstandingToken | None = OutstandingToken.objects.filter(jti=jti).first()
    if outstanding is not None:
        BlacklistedToken.objects.get_or_create(token=outstanding)
