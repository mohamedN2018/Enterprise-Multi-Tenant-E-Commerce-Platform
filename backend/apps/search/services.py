"""Product search service with a per-store, versioned result cache.

Results are cached (Redis in production, locmem in tests) under a key that
embeds a per-store version counter. Catalog writes bump the counter (see
``receivers``), which invalidates every cached query for that store at once —
no key enumeration required.
"""

from __future__ import annotations

import hashlib
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.cache import cache

from apps.search.backends import get_search_backend


def _version_key(store_id) -> str:
    return f"search:ver:{store_id}"


class ProductSearchService:
    def search(
        self, *, store, query: str, min_price=None, max_price=None, limit=None
    ) -> list[dict]:
        query = (query or "").strip()
        limit = limit or settings.SEARCH["MAX_RESULTS"]
        min_price = self._to_decimal(min_price)
        max_price = self._to_decimal(max_price)

        cache_key = self._key(store, query, min_price, max_price, limit)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        products = get_search_backend().search(
            store=store, query=query, min_price=min_price, max_price=max_price, limit=limit
        )
        results = [self._to_dict(store, product) for product in products]
        cache.set(cache_key, results, timeout=settings.SEARCH["CACHE_TTL"])
        return results

    # --- Cache versioning ---
    @staticmethod
    def version(store) -> int:
        return cache.get(_version_key(store.id), 1)

    @classmethod
    def invalidate(cls, *, store) -> None:
        cache.set(_version_key(store.id), cls.version(store) + 1, timeout=None)

    # --- Internals ---
    def _key(self, store, query, min_price, max_price, limit) -> str:
        raw = f"{query}|{min_price}|{max_price}|{limit}"
        digest = hashlib.md5(raw.encode()).hexdigest()
        return f"search:{store.id}:v{self.version(store)}:{digest}"

    @staticmethod
    def _to_dict(store, product) -> dict:
        min_price = (
            product.variants.filter(is_active=True)
            .order_by("price")
            .values_list("price", flat=True)
            .first()
        )
        return {
            "id": str(product.id),
            "name": product.name,
            "slug": product.slug,
            "description": product.description,
            "min_price": str(min_price) if min_price is not None else None,
            "currency": store.currency,
        }

    @staticmethod
    def _to_decimal(value):
        if value in (None, ""):
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None
