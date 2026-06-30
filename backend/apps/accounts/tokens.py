"""Helpers for one-time token generation & hashing.

Raw tokens are sent to the user (email link); only their SHA-256 hash is stored,
so a database leak does not expose usable tokens.
"""

from __future__ import annotations

import hashlib
import secrets

#: Number of random bytes; token_urlsafe yields ~1.3 chars per byte.
_TOKEN_BYTES = 48


def generate_raw_token() -> str:
    """Return a cryptographically secure, URL-safe random token."""
    return secrets.token_urlsafe(_TOKEN_BYTES)


def hash_token(raw_token: str) -> str:
    """Return the hex SHA-256 digest used for storage and lookup."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
