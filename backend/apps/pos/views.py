"""Cashier (POS) API.

Two audiences, two auth schemes:
  * Management (seller console): create/rotate the key and set the webhook.
    Session/JWT auth + store membership, gated by ``require_write``.
  * Cashier (machine): report in-store sales and read stock levels. Authenticated
    by the per-store API key (:class:`PosApiKeyAuthentication`).
"""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.exceptions import NotFoundError
from apps.core.mixins import BaseAPIView
from apps.core.responses import APIResponse
from apps.pos.authentication import HasPosConnection, PosApiKeyAuthentication
from apps.pos.models import PosConnection, PosSupplierConnection
from apps.pos.serializers import (
    PosConnectionCreateSerializer,
    PosConnectionSerializer,
    PosConnectionUpdateSerializer,
    PosSaleSerializer,
    PosSupplierConnectSerializer,
    PosSupplierSerializer,
)
from apps.pos.services import PosService, PosSupplierService
from apps.stores.context import StoreContextMixin

# Linking a cashier is a store-settings action.
_POS_AREA = "settings"


# --- Management (seller console) -------------------------------------------
@extend_schema(tags=["POS"])
class PosConnectionView(StoreContextMixin, BaseAPIView):
    """View / create / update / unlink the store's cashier connection."""

    def _connection(self) -> PosConnection | None:
        return PosConnection.all_objects.filter(store=self.store, is_deleted=False).first()

    def get(self, request: Request) -> Response:
        connection = self._connection()
        data = PosConnectionSerializer(connection).data if connection else None
        return APIResponse.success(data)

    def post(self, request: Request) -> Response:
        self.require_write(area=_POS_AREA)
        payload = PosConnectionCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        connection, api_key = PosService().create_connection(
            store=self.store, **payload.validated_data
        )
        return APIResponse.success(
            {"connection": PosConnectionSerializer(connection).data, "api_key": api_key},
            message="Cashier linked. Copy the API key now — it won't be shown again.",
            status_code=201,
        )

    def patch(self, request: Request) -> Response:
        self.require_write(area=_POS_AREA)
        connection = self._connection()
        if connection is None:
            raise NotFoundError("No cashier is linked to this store.")
        payload = PosConnectionUpdateSerializer(data=request.data, partial=True)
        payload.is_valid(raise_exception=True)
        connection = PosService().update_connection(
            connection=connection, data=payload.validated_data
        )
        return APIResponse.success(
            PosConnectionSerializer(connection).data, message="Cashier connection updated."
        )

    def delete(self, request: Request) -> Response:
        self.require_write(area=_POS_AREA)
        connection = self._connection()
        if connection is None:
            raise NotFoundError("No cashier is linked to this store.")
        connection.delete()
        return APIResponse.success(None, message="Cashier unlinked.")


@extend_schema(tags=["POS"])
class PosConnectionRotateView(StoreContextMixin, BaseAPIView):
    def post(self, request: Request) -> Response:
        self.require_write(area=_POS_AREA)
        connection = PosConnection.all_objects.filter(
            store=self.store, is_deleted=False
        ).first()
        if connection is None:
            raise NotFoundError("No cashier is linked to this store.")
        api_key = PosService().rotate_key(connection=connection)
        return APIResponse.success(
            {"connection": PosConnectionSerializer(connection).data, "api_key": api_key},
            message="A new key was issued. The previous key no longer works.",
        )


# --- Cashier (machine, API-key auth) ---------------------------------------
class _PosMachineView(BaseAPIView):
    authentication_classes = [PosApiKeyAuthentication]
    permission_classes = [HasPosConnection]


@extend_schema(tags=["POS"])
class PosSaleView(_PosMachineView):
    """The cashier reports an in-store sale; the shared warehouse deducts."""

    def post(self, request: Request) -> Response:
        payload = PosSaleSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        results = PosService().record_sale(
            connection=request.pos_connection,
            items=payload.validated_data["items"],
            reference=payload.validated_data.get("reference", ""),
        )
        return APIResponse.success({"items": results}, message="Sale recorded.")


@extend_schema(tags=["POS"])
class PosStockView(_PosMachineView):
    """The cashier pulls current stock levels (optionally ``?sku=a,b,c``)."""

    def get(self, request: Request) -> Response:
        raw = request.query_params.get("sku", "")
        skus = [s.strip() for s in raw.split(",") if s.strip()] or None
        snapshot = PosService().stock_snapshot(
            store=request.pos_connection.store, skus=skus
        )
        return APIResponse.success({"items": snapshot})


# --- Outbound: import products FROM an external POS supplier ----------------
@extend_schema(tags=["POS"])
class PosSupplierView(StoreContextMixin, BaseAPIView):
    """View / connect / disconnect the store's link to an external POS supplier."""

    def get_throttles(self):
        # Rate-limit only the expensive server-fetch (connect); reads stay cheap.
        if self.request.method == "POST":
            self.throttle_scope = "pos_connect"
        return super().get_throttles()

    def _connection(self) -> PosSupplierConnection | None:
        return PosSupplierConnection.all_objects.filter(store=self.store, is_deleted=False).first()

    def get(self, request: Request) -> Response:
        connection = self._connection()
        data = PosSupplierSerializer(connection).data if connection else None
        return APIResponse.success(data)

    def post(self, request: Request) -> Response:
        self.require_write(area=_POS_AREA)
        payload = PosSupplierConnectSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        connection = PosSupplierService().connect(store=self.store, **payload.validated_data)
        return APIResponse.success(
            PosSupplierSerializer(connection).data, message="Connected to the cashier system."
        )

    def delete(self, request: Request) -> Response:
        self.require_write(area=_POS_AREA)
        connection = self._connection()
        if connection is None:
            raise NotFoundError("No cashier system is connected to this store.")
        PosSupplierService().disconnect(connection=connection)
        return APIResponse.success(None, message="Disconnected from the cashier system.")


@extend_schema(tags=["POS"])
class PosSupplierImportView(StoreContextMixin, BaseAPIView):
    """Pull the supplier's catalog and upsert it into this store."""

    throttle_scope = "pos_import"

    def post(self, request: Request) -> Response:
        self.require_write(area=_POS_AREA)
        connection = PosSupplierConnection.all_objects.filter(
            store=self.store, is_deleted=False
        ).first()
        if connection is None:
            raise NotFoundError("Connect a cashier system before importing.")
        summary = PosSupplierService().import_products(connection=connection)
        return APIResponse.success(
            {"connection": PosSupplierSerializer(connection).data, "summary": summary},
            message="Products imported.",
        )
