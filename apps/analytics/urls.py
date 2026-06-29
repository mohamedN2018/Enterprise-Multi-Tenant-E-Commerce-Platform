"""Analytics API routes (mounted under /api/v1/analytics/). Store via header."""

from django.urls import path

from apps.analytics import views

app_name = "analytics"

urlpatterns = [
    path("events/", views.AnalyticsEventListView.as_view(), name="event-list"),
    path("summary/", views.AnalyticsSummaryView.as_view(), name="summary"),
]
