"""Reusable validators."""
from __future__ import annotations

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.deconstruct import deconstructible

# E.164-style phone numbers (e.g. +201234567890).
phone_validator = RegexValidator(
    regex=r"^\+?[1-9]\d{7,14}$",
    message="Enter a valid phone number in international format, e.g. +201234567890.",
)


@deconstructible
class FileSizeValidator:
    """Reject files larger than ``max_mb`` megabytes.

    ``@deconstructible`` makes it migration-serialisable when attached to a field.
    """

    def __init__(self, max_mb: float) -> None:
        self.max_mb = max_mb

    def __call__(self, file) -> None:
        max_bytes = int(self.max_mb * 1024 * 1024)
        if file.size > max_bytes:
            raise ValidationError(
                f"File too large. Maximum allowed size is {self.max_mb} MB."
            )

    def __eq__(self, other) -> bool:
        return isinstance(other, FileSizeValidator) and self.max_mb == other.max_mb
