"""Inventory API views.

Warehouse CRUD + stock operations (receive/adjust/transfer), stock & movement
listings, and a low-stock report. All store-scoped via ``StoreContextMixin``;
mutations require manager/owner and go through ``InventoryService``.
"""

from __future__ import annotations

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.catalog.models import ProductVariant
from apps.core.exceptions import ConflictError, ValidationError
from apps.core.mixins import BaseAPIView, BaseGenericAPIView
from apps.core.responses import APIResponse
from apps.inventory.models import StockMovement, Warehouse
from apps.inventory.repositories import StockItemRepository
from apps.inventory.serializers import (
    AdjustStockSerializer,
    ReceiveStockSerializer,
    StockItemSerializer,
    StockMovementSerializer,
    TransferStockSerializer,
    WarehouseSerializer,
)
from apps.inventory.services import InventoryService
from apps.stores.context import StoreContextMixin


class _ResolveMixin:
    """Resolve variant/warehouse ids against the active (scoped) store."""

    def _variant(self, variant_id) -> ProductVariant:
        variant = ProductVariant.objects.filter(id=variant_id).first()
        if variant is None:
            raise ValidationError(
                "Variant not found in this store.",
                errors={"variant_id": ["Not found in this store."]},
            )
        return variant

    def _warehouse(self, warehouse_id, *, field="warehouse_id") -> Warehouse:
        warehouse = Warehouse.objects.filter(id=warehouse_id).first()
        if warehouse is None:
            raise ValidationError(
                "Warehouse not found in this store.",
                errors={field: ["Not found in this store."]},
            )
        return warehouse


def _assert_code_unique(*, store, code, exclude_pk=None) -> None:
    qs = Warehouse.all_objects.filter(store=store, code=code, is_deleted=False)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    if qs.exists():
        raise ConflictError(
            "A warehouse with this code already exists in this store.", code="code_taken"
        )


# --- Warehouses ------------------------------------------------------------
class WarehouseListCreateView(StoreContextMixin, BaseGenericAPIView, generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WarehouseSerializer
    search_fields = ("name", "code")
    filterset_fields = ("is_active", "is_default")

    def get_queryset(self):
        return Warehouse.objects.all()

    def perform_create(self, serializer):
        self.require_write()
        _assert_code_unique(store=self.store, code=serializer.validated_data["code"])
        warehouse = serializer.save(store=self.store)
        InventoryService.ensure_single_default(store=self.store, warehouse=warehouse)


class WarehouseDetailView(
    StoreContextMixin, BaseGenericAPIView, generics.RetrieveUpdateDestroyAPIView
):
    permission_classes = [IsAuthenticated]
    serializer_class = WarehouseSerializer
    lookup_url_kwarg = "warehouse_id"

    def get_queryset(self):
        return Warehouse.objects.all()

    def perform_update(self, serializer):
        self.require_write()
        code = serializer.validated_data.get("code")
        if code:
            _assert_code_unique(store=self.store, code=code, exclude_pk=serializer.instance.pk)
        warehouse = serializer.save()
        InventoryService.ensure_single_default(store=self.store, warehouse=warehouse)

    def perform_destroy(self, instance):
        self.require_write()
        instance.delete()


# --- Stock & movement listings --------------------------------------------
class StockItemListView(StoreContextMixin, BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StockItemSerializer
    filterset_fields = ("warehouse", "variant")

    def get_queryset(self):
        return StockItemRepository().with_relations()


class LowStockListView(StoreContextMixin, BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StockItemSerializer

    def get_queryset(self):
        return StockItemRepository().low_stock()


class StockMovementListView(StoreContextMixin, BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StockMovementSerializer
    filterset_fields = ("warehouse", "variant", "movement_type")

    def get_queryset(self):
        return StockMovement.objects.all()


# --- Operations ------------------------------------------------------------
class ReceiveStockView(_ResolveMixin, StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        self.require_write()
        data = _validated(ReceiveStockSerializer, request)
        item = InventoryService().receive(
            store=self.store,
            variant=self._variant(data["variant_id"]),
            warehouse=self._warehouse(data["warehouse_id"]),
            quantity=data["quantity"],
            reference=data["reference"],
            note=data["note"],
        )
        return APIResponse.success(StockItemSerializer(item).data, message="Stock received.")


class AdjustStockView(_ResolveMixin, StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        self.require_write()
        data = _validated(AdjustStockSerializer, request)
        item = InventoryService().adjust(
            store=self.store,
            variant=self._variant(data["variant_id"]),
            warehouse=self._warehouse(data["warehouse_id"]),
            new_quantity=data["quantity"],
            note=data["note"],
        )
        return APIResponse.success(StockItemSerializer(item).data, message="Stock adjusted.")


class TransferStockView(_ResolveMixin, StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        self.require_write()
        data = _validated(TransferStockSerializer, request)
        source, destination = InventoryService().transfer(
            store=self.store,
            variant=self._variant(data["variant_id"]),
            from_warehouse=self._warehouse(data["from_warehouse_id"], field="from_warehouse_id"),
            to_warehouse=self._warehouse(data["to_warehouse_id"], field="to_warehouse_id"),
            quantity=data["quantity"],
            note=data["note"],
        )
        return APIResponse.success(
            {
                "source": StockItemSerializer(source).data,
                "destination": StockItemSerializer(destination).data,
            },
            message="Stock transferred.",
        )


def _validated(serializer_class, request) -> dict:
    serializer = serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data
