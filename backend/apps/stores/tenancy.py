"""Tenant resolution: map an incoming request to its ``Store``.

Wired into ``CurrentRequestMiddleware`` via ``settings.TENANT_RESOLVER``. Resolution
order: ``X-Store-Id`` header, then ``X-Store-Slug`` header, then subdomain. Returns
``None`` (and performs no DB query) when the request carries no store hint — so
storeless endpoints (auth, docs) pay nothing.
"""

from __future__ import annotations

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError

_IGNORED_SUBDOMAINS = {"www", "api", "admin", "localhost"}


def store_cache_keys(*, store_id=None, slug=None) -> list[str]:
    keys = []
    if store_id:
        keys.append(f"tenant:id:{store_id}")
    if slug:
        keys.append(f"tenant:slug:{slug}")
    return keys


def _ttl() -> int:
    return int(getattr(settings, "TENANT_CACHE_TTL", 60))


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

    # Per-request hot path: cache the resolved store (with its settings) so most
    # store-scoped calls skip the lookup. Invalidated on Store/StoreSettings save
    # (see apps.stores.receivers). Only successful resolutions are cached.
    cache_key = f"tenant:id:{store_id}" if store_id else f"tenant:slug:{store_slug}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        queryset = Store.objects.select_related("settings")
        store = (
            queryset.filter(id=store_id).first()
            if store_id
            else queryset.filter(slug=store_slug).first()
        )
    except (ValueError, ValidationError, TypeError):
        # Malformed identifier (e.g. non-UUID) -> treat as no tenant.
        return None

    if store is not None:
        cache.set(cache_key, store, _ttl())
    return store
