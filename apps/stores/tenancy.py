"""Tenant resolution: map an incoming request to its ``Store``.

Wired into ``CurrentRequestMiddleware`` via ``settings.TENANT_RESOLVER``. Resolution
order: ``X-Store-Id`` header, then ``X-Store-Slug`` header, then subdomain. Returns
``None`` (and performs no DB query) when the request carries no store hint — so
storeless endpoints (auth, docs) pay nothing.
"""

from __future__ import annotations

from django.core.exceptions import ValidationError

_IGNORED_SUBDOMAINS = {"www", "api", "admin", "localhost"}


def _slug_from_host(request) -> str | None:
    host = request.get_host().split(":")[0]
    labels = host.split(".")
    # Require a real subdomain (e.g. acme.example.com), not a bare/2-label host.
    if len(labels) < 3:
        return None
    candidate = labels[0]
    return None if candidate in _IGNORED_SUBDOMAINS else candidate


def resolve_store(request):
    # Imported lazily to keep the shared kernel free of domain imports.
    from apps.stores.models import Store

    store_id = request.headers.get("X-Store-Id")
    store_slug = request.headers.get("X-Store-Slug") or _slug_from_host(request)

    if not store_id and not store_slug:
        return None

    try:
        if store_id:
            return Store.objects.filter(id=store_id).first()
        return Store.objects.filter(slug=store_slug).first()
    except (ValueError, ValidationError, TypeError):
        # Malformed identifier (e.g. non-UUID) -> treat as no tenant.
        return None
