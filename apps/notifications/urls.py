"""Notification API routes (mounted under /api/v1/notifications/). Store via header."""

from django.urls import path

from apps.notifications import views

app_name = "notifications"

urlpatterns = [
    path("", views.NotificationListView.as_view(), name="list"),
    path("unread-count/", views.NotificationUnreadCountView.as_view(), name="unread-count"),
    path("read-all/", views.NotificationReadAllView.as_view(), name="read-all"),
    path("preferences/", views.NotificationPreferenceView.as_view(), name="preferences"),
    path("<uuid:notification_id>/read/", views.NotificationReadView.as_view(), name="read"),
]
