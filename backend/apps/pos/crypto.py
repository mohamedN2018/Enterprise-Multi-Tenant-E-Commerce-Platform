"""Symmetric encryption for secrets at rest (the POS supplier API key).

Fernet (AES-128-CBC + HMAC) with a key derived from ``FIELD_ENCRYPTION_KEY`` if
set, else from ``SECRET_KEY``. Note: rotating that secret makes existing
ciphertext undecryptable — sellers would simply re-enter their key.
"""

from __future__ import annotations

import base64
import hashlib
from functools import lru_cache

from django.conf import settings


@lru_cache(maxsize=1)
def _fernet():
    from cryptography.fernet import Fernet

    secret = getattr(settings, "FIELD_ENCRYPTION_KEY", None) or settings.SECRET_KEY
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
    return Fernet(key)


def encrypt(text: str) -> str:
    if not text:
        return text
    return _fernet().encrypt(text.encode()).decode()


def decrypt(token: str) -> str:
    """Decrypt, falling back to the raw value for legacy plaintext rows written
    before encryption was introduced (so the transition needs no data migration)."""
    if not token:
        return token
    from cryptography.fernet import InvalidToken

    try:
        return _fernet().decrypt(token.encode()).decode()
    except (InvalidToken, ValueError):
        return token
