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

# Raster image formats only. SVG is deliberately excluded — it is XML and can
# carry <script>, so serving an uploaded SVG inline is a stored-XSS vector.
ALLOWED_IMAGE_CONTENT_TYPES = frozenset(
    {"image/jpeg", "image/png", "image/webp", "image/gif"}
)
ALLOWED_IMAGE_EXTENSIONS = frozenset({"jpg", "jpeg", "png", "webp", "gif"})
MAX_IMAGE_UPLOAD_MB = 5


def validate_image_upload(file, *, max_mb: float = MAX_IMAGE_UPLOAD_MB) -> None:
    """Validate an uploaded image before persisting it.

    Guards against unbounded uploads (disk/DoS), content-type spoofing, and
    disguised non-images (e.g. an SVG/HTML payload renamed ``.png``). Raises the
    domain :class:`apps.core.exceptions.ValidationError` (HTTP 400) on failure.

    ``product.save()`` does NOT run field validators, so callers accepting an
    upload directly (outside a serializer/``full_clean``) must call this.
    """
    from apps.core.exceptions import ValidationError as DomainValidationError

    def _reject(message: str) -> None:
        raise DomainValidationError(
            message, code="invalid_image", errors={"image": [message]}
        )

    max_bytes = int(max_mb * 1024 * 1024)
    if file.size > max_bytes:
        _reject(f"Image too large. Maximum allowed size is {max_mb:g} MB.")

    content_type = (getattr(file, "content_type", "") or "").lower()
    if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        _reject("Unsupported image type. Use JPG, PNG, WebP or GIF.")

    name = getattr(file, "name", "") or ""
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        _reject("Unsupported image extension. Use .jpg, .png, .webp or .gif.")

    # Verify the bytes actually decode as an image (defeats a spoofed
    # Content-Type header on a non-image / disguised payload).
    try:
        from PIL import Image

        file.seek(0)
        Image.open(file).verify()
    except DomainValidationError:
        raise
    except Exception:  # noqa: BLE001 — any decode failure means "not an image"
        _reject("The uploaded file is not a valid image.")
    finally:
        try:
            file.seek(0)
        except Exception:  # noqa: BLE001
            pass


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
            raise ValidationError(f"File too large. Maximum allowed size is {self.max_mb} MB.")

    def __eq__(self, other) -> bool:
        return isinstance(other, FileSizeValidator) and self.max_mb == other.max_mb
