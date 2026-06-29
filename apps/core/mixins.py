"""Reusable view mixins."""
from __future__ import annotations

from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView

from apps.core import tenancy


class ActorContextMixin:
    """Refresh the request-scoped actor after DRF authentication.

    ``CurrentRequestMiddleware`` binds the *session* user early in the cycle,
    but DRF resolves the real authenticated user (e.g. via JWT) later, during
    ``initial()``. Re-binding here ensures audit stamping uses the correct actor.
    """

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        tenancy.set_current_user(getattr(request, "user", None))


class BaseAPIView(ActorContextMixin, APIView):
    """APIView with actor-context binding. Use for non-model endpoints."""


class BaseGenericAPIView(ActorContextMixin, GenericAPIView):
    """GenericAPIView with actor-context binding. Base for CRUD endpoints."""
