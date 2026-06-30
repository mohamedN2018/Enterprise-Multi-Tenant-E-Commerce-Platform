"""Pagination that emits the project's envelope with rich ``meta.pagination``."""

from __future__ import annotations

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data) -> Response:
        return Response(
            {
                "success": True,
                "message": "OK",
                "data": data,
                "errors": None,
                "meta": {
                    "pagination": {
                        "count": self.page.paginator.count,
                        "page": self.page.number,
                        "page_size": self.get_page_size(self.request),
                        "total_pages": self.page.paginator.num_pages,
                        "next": self.get_next_link(),
                        "previous": self.get_previous_link(),
                    }
                },
            }
        )
