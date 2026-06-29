"""Notification API (buyer/staff: each user manages their own inbox + prefs)."""

from __future__ import annotations

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.exceptions import NotFoundError
from apps.core.mixins import BaseAPIView, BaseGenericAPIView
from apps.core.responses import APIResponse
from apps.notifications.models import Notification
from apps.notifications.serializers import (
    NotificationPreferenceSerializer,
    NotificationSerializer,
)
from apps.notifications.services import NotificationService
from apps.stores.context import RequireStoreMixin


class NotificationListView(RequireStoreMixin, BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    filterset_fields = ("is_read", "event_type")

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class NotificationReadView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, notification_id) -> Response:
        notification = Notification.objects.filter(
            id=notification_id, recipient=request.user
        ).first()
        if notification is None:
            raise NotFoundError("Notification not found.")
        notification = NotificationService().mark_read(notification=notification)
        return APIResponse.success(
            NotificationSerializer(notification).data, message="Marked read."
        )


class NotificationReadAllView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        count = NotificationService().mark_all_read(store=self.store, user=request.user)
        return APIResponse.success({"updated": count}, message="All notifications marked read.")


class NotificationUnreadCountView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        count = NotificationService().unread_count(store=self.store, user=request.user)
        return APIResponse.success({"unread": count})


class NotificationPreferenceView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        preference = NotificationService().get_preference(store=self.store, user=request.user)
        return APIResponse.success(NotificationPreferenceSerializer(preference).data)

    def put(self, request: Request) -> Response:
        serializer = NotificationPreferenceSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        preference = NotificationService().update_preference(
            store=self.store, user=request.user, data=serializer.validated_data
        )
        return APIResponse.success(
            NotificationPreferenceSerializer(preference).data, message="Preferences updated."
        )
