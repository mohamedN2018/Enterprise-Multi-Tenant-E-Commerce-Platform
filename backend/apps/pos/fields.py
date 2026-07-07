"""Model field that transparently encrypts its value at rest."""

from __future__ import annotations

from django.db import models

from apps.pos import crypto


class EncryptedTextField(models.TextField):
    """Stores its value Fernet-encrypted; decrypts on load. Never filter/index on
    it (each write produces different ciphertext). Legacy plaintext reads through
    unchanged (see :func:`apps.pos.crypto.decrypt`)."""

    def from_db_value(self, value, expression, connection):
        return crypto.decrypt(value) if value else value

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        return crypto.encrypt(value) if value else value
