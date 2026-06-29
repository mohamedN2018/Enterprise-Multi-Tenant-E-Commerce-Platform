"""Search API (buyer-facing): product search within the active store."""

from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.mixins import BaseAPIView
from apps.core.responses import APIResponse
from apps.search.services import ProductSearchService
from apps.stores.context import RequireStoreMixin


class ProductSearchView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        params = request.query_params
        results = ProductSearchService().search(
            store=self.store,
            query=params.get("q", ""),
            min_price=params.get("min_price"),
            max_price=params.get("max_price"),
        )
        return APIResponse.success(results, meta={"count": len(results)})
