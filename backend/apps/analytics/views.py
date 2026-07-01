"""Analytics API (staff): event feed + store summary. Requires store membership."""

from __future__ import annotations

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.analytics.models import AnalyticsEvent
from apps.analytics.serializers import AnalyticsEventSerializer, SummaryQuerySerializer
from apps.analytics.services import AnalyticsService
from apps.core.mixins import BaseAPIView, BaseGenericAPIView
from apps.core.responses import APIResponse
from apps.stores.context import StoreContextMixin


class AnalyticsEventListView(StoreContextMixin, BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AnalyticsEventSerializer
    filterset_fields = ("event_type",)

    def get_queryset(self):
        return AnalyticsEvent.objects.all()


class AnalyticsSummaryView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        query = SummaryQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        summary = AnalyticsService().summary(
            store=self.store,
            start=query.validated_data.get("start"),
            end=query.validated_data.get("end"),
        )
        return APIResponse.success(summary)


class AnalyticsDashboardView(StoreContextMixin, BaseAPIView):
    """Rich store snapshot (KPIs, recent orders, top products, alerts)."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return APIResponse.success(AnalyticsService().dashboard(store=self.store))
