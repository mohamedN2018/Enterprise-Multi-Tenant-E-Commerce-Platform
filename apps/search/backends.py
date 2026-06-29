"""Pluggable product-search backends.

The default :class:`DatabaseSearchBackend` is portable (works on SQLite and
PostgreSQL) and queries the catalog directly. Swapping in an Elasticsearch /
OpenSearch backend is a matter of pointing ``settings.SEARCH["BACKEND"]`` at an
implementation with the same ``search`` signature — callers (the service/view)
never change.
"""

from __future__ import annotations

from django.conf import settings
from django.db.models import Q
from django.utils.module_loading import import_string

from apps.catalog.models import Product, ProductStatus


class SearchBackend:
    """Interface every search backend implements."""

    def search(self, *, store, query, min_price=None, max_price=None, limit=20):
        raise NotImplementedError


class DatabaseSearchBackend(SearchBackend):
    def search(self, *, store, query, min_price=None, max_price=None, limit=20):
        queryset = Product.objects.filter(store=store, status=ProductStatus.PUBLISHED)
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(variants__sku__icontains=query)
            )
        if min_price is not None:
            queryset = queryset.filter(variants__price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(variants__price__lte=max_price)
        return list(queryset.distinct().order_by("name")[:limit])


class PostgresSearchBackend(SearchBackend):
    """Full-text search using PostgreSQL's ``tsvector`` ranking.

    A drop-in for :class:`DatabaseSearchBackend` (point ``settings.SEARCH["BACKEND"]``
    here) that ranks matches over the product name and description, with a SKU
    substring fallback. Requires PostgreSQL; the imports are local so the module
    stays importable on any database.
    """

    def search(self, *, store, query, min_price=None, max_price=None, limit=20):
        from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

        queryset = Product.objects.filter(store=store, status=ProductStatus.PUBLISHED)
        if min_price is not None:
            queryset = queryset.filter(variants__price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(variants__price__lte=max_price)
        if query:
            vector = SearchVector("name", "description")
            queryset = (
                queryset.annotate(rank=SearchRank(vector, SearchQuery(query)))
                .filter(Q(rank__gt=0) | Q(variants__sku__icontains=query))
                .order_by("-rank", "name")
            )
        else:
            queryset = queryset.order_by("name")
        return list(queryset.distinct()[:limit])


def get_search_backend() -> SearchBackend:
    return import_string(settings.SEARCH["BACKEND"])()
