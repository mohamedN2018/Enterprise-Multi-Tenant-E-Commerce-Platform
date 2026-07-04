"""Content localisation helpers.

The platform is Arabic-first: the primary ``name``/``description`` fields hold
Arabic, with optional ``*_en`` English counterparts. Storefront serializers
return the value matching the request's ``Accept-Language`` header (defaulting to
Arabic), so shoppers always read content in their chosen language.
"""

from __future__ import annotations


def request_locale(context) -> str:
    """'en' if the request asked for English, else 'ar' (the default)."""
    request = context.get("request") if context else None
    lang = ""
    if request is not None:
        lang = request.headers.get("Accept-Language", "") or ""
    return "en" if lang.strip().lower().startswith("en") else "ar"


def localized(obj, field: str, context) -> str:
    """Return the localised value of ``field`` (falls back to the primary)."""
    if request_locale(context) == "en":
        return getattr(obj, f"{field}_en", "") or getattr(obj, field, "") or ""
    return getattr(obj, field, "") or ""
