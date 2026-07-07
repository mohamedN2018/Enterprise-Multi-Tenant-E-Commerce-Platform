"""API-key primitives for the cashier integration.

A key is shown to the seller exactly once (on create/rotate); we persist only its
SHA-256 hash plus a short, non-secret prefix used to look the row up quickly.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

# Length of the stored/display prefix. Includes the "pos_" tag plus a few chars,
# enough to identify a key without revealing it.
PREFIX_LEN = 12


def generate_key() -> str:
    return "pos_" + secrets.token_urlsafe(32)


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def key_prefix(key: str) -> str:
    return key[:PREFIX_LEN]


def verify_key(key: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_key(key), hashed)


def sign_payload(secret: str, body: bytes) -> str:
    """HMAC-SHA256 hex digest so the cashier can verify an outbound webhook."""
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
