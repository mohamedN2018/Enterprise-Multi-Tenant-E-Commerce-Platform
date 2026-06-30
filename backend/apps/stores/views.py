"""Stores API views.

Thin HTTP layer over services; RBAC enforced via :class:`StoreAccessMixin`.
"""

from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.mixins import BaseAPIView, BaseGenericAPIView
from apps.core.responses import APIResponse
from apps.stores.access import MANAGER_OR_OWNER, OWNER_ONLY, StoreAccessMixin
from apps.stores.repositories import StoreRepository
from apps.stores.serializers import (
    MembershipCreateSerializer,
    MembershipSerializer,
    MembershipUpdateSerializer,
    StoreCreateSerializer,
    StoreSerializer,
    StoreSettingsSerializer,
    StoreUpdateSerializer,
)
from apps.stores.services import MembershipService, StoreService


class StoreListCreateView(BaseGenericAPIView, generics.ListCreateAPIView):
    """GET: stores the caller belongs to. POST: create a store (caller = owner)."""

    permission_classes = [IsAuthenticated]
    serializer_class = StoreSerializer

    def get_queryset(self):
        return StoreRepository().for_member(self.request.user)

    @extend_schema(request=StoreCreateSerializer, responses={201: StoreSerializer}, tags=["stores"])
    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = StoreCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        store = StoreService().create_store(owner=request.user, data=serializer.validated_data)
        return APIResponse.success(
            data=StoreSerializer(store).data,
            message="Store created.",
            status_code=status.HTTP_201_CREATED,
        )


class StoreDetailView(StoreAccessMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: StoreSerializer}, tags=["stores"])
    def get(self, request: Request, store_id) -> Response:
        store = self.load_store(store_id)
        return APIResponse.success(StoreSerializer(store).data)

    @extend_schema(request=StoreUpdateSerializer, responses={200: StoreSerializer}, tags=["stores"])
    def patch(self, request: Request, store_id) -> Response:
        store = self.load_store(store_id, roles=MANAGER_OR_OWNER)
        serializer = StoreUpdateSerializer(instance=store, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        store = StoreService().update_store(store=store, data=serializer.validated_data)
        return APIResponse.success(StoreSerializer(store).data, message="Store updated.")

    @extend_schema(responses={200: OpenApiResponse()}, tags=["stores"])
    def delete(self, request: Request, store_id) -> Response:
        store = self.load_store(store_id, roles=OWNER_ONLY)
        StoreService().delete_store(store=store)
        return APIResponse.success(message="Store deleted.")


class StoreSettingsView(StoreAccessMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: StoreSettingsSerializer}, tags=["stores"])
    def get(self, request: Request, store_id) -> Response:
        store = self.load_store(store_id)
        return APIResponse.success(StoreSettingsSerializer(store.settings).data)

    @extend_schema(
        request=StoreSettingsSerializer, responses={200: StoreSettingsSerializer}, tags=["stores"]
    )
    def patch(self, request: Request, store_id) -> Response:
        store = self.load_store(store_id, roles=MANAGER_OR_OWNER)
        serializer = StoreSettingsSerializer(
            instance=store.settings, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        settings_obj = StoreService().update_settings(store=store, data=serializer.validated_data)
        return APIResponse.success(
            StoreSettingsSerializer(settings_obj).data, message="Settings updated."
        )


class MemberListCreateView(StoreAccessMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: MembershipSerializer(many=True)}, tags=["stores"])
    def get(self, request: Request, store_id) -> Response:
        store = self.load_store(store_id, roles=MANAGER_OR_OWNER)
        members = MembershipService().list_members(store)
        return APIResponse.success(MembershipSerializer(members, many=True).data)

    @extend_schema(
        request=MembershipCreateSerializer, responses={201: MembershipSerializer}, tags=["stores"]
    )
    def post(self, request: Request, store_id) -> Response:
        store = self.load_store(store_id, roles=MANAGER_OR_OWNER)
        serializer = MembershipCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = MembershipService().add_member(
            store=store,
            email=serializer.validated_data["email"],
            role=serializer.validated_data["role"],
            invited_by=request.user,
        )
        return APIResponse.success(
            MembershipSerializer(membership).data,
            message="Member added.",
            status_code=status.HTTP_201_CREATED,
        )


class MemberDetailView(StoreAccessMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=MembershipUpdateSerializer, responses={200: MembershipSerializer}, tags=["stores"]
    )
    def patch(self, request: Request, store_id, member_id) -> Response:
        store = self.load_store(store_id, roles=OWNER_ONLY)
        service = MembershipService()
        membership = service.get_member(store=store, member_id=member_id)
        serializer = MembershipUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = service.change_role(
            store=store, membership=membership, role=serializer.validated_data["role"]
        )
        return APIResponse.success(MembershipSerializer(membership).data, message="Role updated.")

    @extend_schema(responses={200: OpenApiResponse()}, tags=["stores"])
    def delete(self, request: Request, store_id, member_id) -> Response:
        store = self.load_store(store_id, roles=OWNER_ONLY)
        service = MembershipService()
        membership = service.get_member(store=store, member_id=member_id)
        service.remove_member(store=store, membership=membership)
        return APIResponse.success(message="Member removed.")
