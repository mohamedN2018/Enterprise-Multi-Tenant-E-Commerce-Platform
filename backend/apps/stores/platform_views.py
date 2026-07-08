"""Platform (super-admin) API: oversee and manage every store and seller.

These endpoints are the only place ownership can be assigned to another user and
where per-seller / per-store limits are configured. Superuser-only.
"""

from __future__ import annotations

from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.models import User
from apps.accounts.repositories import UserRepository
from apps.core.exceptions import NotFoundError, ValidationError
from apps.core.mixins import BaseAPIView
from apps.core.permissions import IsSuperAdmin
from apps.core.responses import APIResponse
from apps.stores.models import LimitRequest, PlatformTheme, Store, StoreRole, StoreStatus
from apps.stores.serializers import (
    DEFAULT_THEME,
    LimitRequestSerializer,
    PlatformSellerCreateSerializer,
    PlatformStoreCreateSerializer,
    PlatformStoreSerializer,
    PlatformStoreUpdateSerializer,
    PlatformThemeSerializer,
    SellerSerializer,
    SellerUpdateSerializer,
)
from apps.stores.services import LimitRequestService, StoreService


def _seller_with_counts(user_id):
    """Reload a user annotated with their live owned-store count."""
    return User.objects.annotate(
        store_count=Count("owned_stores", filter=Q(owned_stores__is_deleted=False), distinct=True)
    ).get(id=user_id)


def _stores_qs():
    """All stores with team-size counts annotated (platform-wide)."""
    return (
        Store.objects.select_related("owner", "settings")
        .annotate(
            member_count=Count(
                "memberships",
                filter=Q(memberships__is_active=True, memberships__is_deleted=False),
                distinct=True,
            ),
            employee_count=Count(
                "memberships",
                filter=Q(
                    memberships__is_active=True,
                    memberships__is_deleted=False,
                    memberships__role=StoreRole.EMPLOYEE,
                ),
                distinct=True,
            ),
            product_count=Count(
                "catalog_product_set",
                filter=Q(catalog_product_set__is_deleted=False),
                distinct=True,
            ),
        )
        .order_by("-created_at")
    )


class PlatformStoreListCreateView(BaseAPIView):
    permission_classes = [IsSuperAdmin]

    @extend_schema(responses={200: PlatformStoreSerializer(many=True)}, tags=["platform"])
    def get(self, request: Request) -> Response:
        stores = _stores_qs()
        return APIResponse.success(PlatformStoreSerializer(stores, many=True).data)

    @extend_schema(
        request=PlatformStoreCreateSerializer,
        responses={201: PlatformStoreSerializer},
        tags=["platform"],
    )
    def post(self, request: Request) -> Response:
        serializer = PlatformStoreCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        owner = UserRepository().get_by_email(data["owner_email"])
        if owner is None:
            raise ValidationError(
                "No user found with this email. Ask the seller to register first.",
                code="user_not_found",
                errors={"owner_email": ["No user found with this email."]},
            )

        store = StoreService().create_store(
            owner=owner,
            data={
                "name": data["name"],
                "description": data.get("description", ""),
                "currency": data.get("currency", "EGP"),
                "country": data.get("country", ""),
            },
        )
        # Admin-created stores go live immediately unless told otherwise.
        target_status = data.get("status", StoreStatus.ACTIVE)
        if target_status != store.status:
            store.status = target_status
            store.save(update_fields=["status", "updated_at"])

        fresh = _stores_qs().get(id=store.id)
        return APIResponse.success(
            PlatformStoreSerializer(fresh).data,
            message="Store created for seller.",
            status_code=status.HTTP_201_CREATED,
        )


class PlatformStoreDetailView(BaseAPIView):
    permission_classes = [IsSuperAdmin]

    def _get(self, store_id) -> Store:
        store = Store.objects.filter(id=store_id).select_related("settings").first()
        if store is None:
            raise NotFoundError("Store not found.")
        return store

    @extend_schema(
        request=PlatformStoreUpdateSerializer,
        responses={200: PlatformStoreSerializer},
        tags=["platform"],
    )
    def patch(self, request: Request, store_id) -> Response:
        store = self._get(store_id)
        serializer = PlatformStoreUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        svc = StoreService()
        if "status" in data:
            svc.update_store(store=store, data={"status": data["status"]})
        if "is_verified" in data:
            store.is_verified = data["is_verified"]
            store.save(update_fields=["is_verified", "updated_at"])
        if "max_employees" in data:
            svc.update_settings(store=store, data={"max_employees": data["max_employees"]})

        fresh = _stores_qs().get(id=store_id)
        return APIResponse.success(PlatformStoreSerializer(fresh).data, message="Store updated.")

    @extend_schema(tags=["platform"])
    def delete(self, request: Request, store_id) -> Response:
        store = self._get(store_id)
        StoreService().delete_store(store=store)
        return APIResponse.success(message="Store deleted.")


class PlatformSellerListView(BaseAPIView):
    permission_classes = [IsSuperAdmin]

    @extend_schema(responses={200: SellerSerializer(many=True)}, tags=["platform"])
    def get(self, request: Request) -> Response:
        qs = User.objects.annotate(
            store_count=Count(
                "owned_stores",
                filter=Q(owned_stores__is_deleted=False),
                distinct=True,
            )
        ).order_by("-store_count", "email")

        search = (request.query_params.get("search") or "").strip()
        if search:
            # Find any user by email (e.g. a newly-contracted seller with no store yet).
            qs = qs.filter(email__icontains=search)
        else:
            # Default view: actual sellers (own at least one store), excluding admins.
            qs = qs.filter(store_count__gt=0, is_superuser=False)

        return APIResponse.success(SellerSerializer(qs, many=True).data)

    @extend_schema(
        request=PlatformSellerCreateSerializer,
        responses={201: SellerSerializer},
        tags=["platform"],
    )
    def post(self, request: Request) -> Response:
        """Create a seller account (admin-vouched, verified) with the default
        one-store allotment, optionally provisioning that first store now."""
        serializer = PlatformSellerCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if UserRepository().get_by_email(data["email"]) is not None:
            raise ValidationError(
                "An account with this email already exists.",
                code="email_taken",
                errors={"email": ["An account with this email already exists."]},
            )

        # Admin creates a contracted seller: active + verified so they can sign
        # in immediately. max_stores keeps its model default of 1 (the rule:
        # one store per seller unless the admin raises it).
        seller = User.objects.create_user(
            email=data["email"], password=data["password"], is_active=True, is_verified=True
        )

        store_name = (data.get("store_name") or "").strip()
        if store_name:
            store = StoreService().create_store(
                owner=seller, data={"name": store_name, "country": data.get("country", "")}
            )
            if store.status != StoreStatus.ACTIVE:
                store.status = StoreStatus.ACTIVE
                store.save(update_fields=["status", "updated_at"])

        return APIResponse.success(
            SellerSerializer(_seller_with_counts(seller.id)).data,
            message="Seller account created.",
            status_code=status.HTTP_201_CREATED,
        )


class PlatformSellerDetailView(BaseAPIView):
    permission_classes = [IsSuperAdmin]

    @extend_schema(responses={200: SellerSerializer}, tags=["platform"])
    def get(self, request: Request, user_id) -> Response:
        """One seller plus every store they own (for the seller detail page)."""
        if not User.objects.filter(id=user_id).exists():
            raise NotFoundError("User not found.")
        data = SellerSerializer(_seller_with_counts(user_id)).data
        stores = _stores_qs().filter(owner_id=user_id)
        data["stores"] = PlatformStoreSerializer(stores, many=True).data
        return APIResponse.success(data)

    @extend_schema(
        request=SellerUpdateSerializer, responses={200: SellerSerializer}, tags=["platform"]
    )
    def patch(self, request: Request, user_id) -> Response:
        user = User.objects.filter(id=user_id).first()
        if user is None:
            raise NotFoundError("User not found.")
        serializer = SellerUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.max_stores = serializer.validated_data["max_stores"]
        user.save(update_fields=["max_stores", "updated_at"])
        return APIResponse.success(
            SellerSerializer(_seller_with_counts(user.id)).data, message="Seller limit updated."
        )


class PlatformRequestListView(BaseAPIView):
    permission_classes = [IsSuperAdmin]

    @extend_schema(responses={200: LimitRequestSerializer(many=True)}, tags=["platform"])
    def get(self, request: Request) -> Response:
        qs = LimitRequest.objects.select_related("requested_by", "store").order_by("-created_at")
        status_filter = (request.query_params.get("status") or "").strip()
        if status_filter:
            qs = qs.filter(status=status_filter)
        return APIResponse.success(LimitRequestSerializer(qs, many=True).data)


class PlatformRequestActionView(BaseAPIView):
    permission_classes = [IsSuperAdmin]
    action = "approve"

    def _get(self, request_id) -> LimitRequest:
        req = LimitRequest.objects.filter(id=request_id).select_related("store", "requested_by").first()
        if req is None:
            raise NotFoundError("Request not found.")
        return req

    @extend_schema(responses={200: LimitRequestSerializer}, tags=["platform"])
    def post(self, request: Request, request_id) -> Response:
        req = self._get(request_id)
        svc = LimitRequestService()
        if self.action == "approve":
            req = svc.approve(request_obj=req, resolver=request.user)
            message = "Request approved."
        else:
            req = svc.reject(request_obj=req, resolver=request.user)
            message = "Request rejected."
        return APIResponse.success(LimitRequestSerializer(req).data, message=message)


class PlatformRequestApproveView(PlatformRequestActionView):
    action = "approve"


class PlatformRequestRejectView(PlatformRequestActionView):
    action = "reject"


@extend_schema(tags=["Platform"])
class PlatformThemeView(BaseAPIView):
    """The marketplace-wide theme. Anyone may read it (the whole site renders with
    it); only the platform admin may change it."""

    def get_permissions(self):
        return [AllowAny()] if self.request.method == "GET" else [IsSuperAdmin()]

    def _current(self) -> dict:
        return {**DEFAULT_THEME, **(PlatformTheme.load().config or {})}

    def get(self, request: Request) -> Response:
        return APIResponse.success(self._current())

    def patch(self, request: Request) -> Response:
        payload = PlatformThemeSerializer(data=request.data, partial=True)
        payload.is_valid(raise_exception=True)
        theme = PlatformTheme.load()
        theme.config = {**DEFAULT_THEME, **(theme.config or {}), **payload.validated_data}
        theme.save()
        return APIResponse.success(theme.config, message="Theme updated.")
