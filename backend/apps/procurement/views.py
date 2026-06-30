"""Procurement API (staff): suppliers, purchase orders, batches, serial numbers.

All store-scoped via ``StoreContextMixin``; mutations require manager/owner and go
through ``ProcurementService``.
"""

from __future__ import annotations

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.catalog.models import ProductVariant
from apps.core.exceptions import NotFoundError, ValidationError
from apps.core.mixins import BaseAPIView, BaseGenericAPIView
from apps.core.responses import APIResponse
from apps.inventory.models import Warehouse
from apps.procurement.models import (
    BillOfMaterials,
    PurchaseOrder,
    SerialNumber,
    StockBatch,
    Supplier,
    WorkOrder,
)
from apps.procurement.serializers import (
    AddBOMComponentSerializer,
    BillOfMaterialsSerializer,
    BOMComponentSerializer,
    CreateBOMSerializer,
    CreatePurchaseOrderSerializer,
    CreateWorkOrderSerializer,
    PurchaseOrderSerializer,
    ReceivePurchaseOrderSerializer,
    RegisterSerialsSerializer,
    SerialNumberSerializer,
    StockBatchSerializer,
    SupplierSerializer,
    UpdateSerialStatusSerializer,
    WorkOrderSerializer,
)
from apps.procurement.services import ManufacturingService, ProcurementService
from apps.stores.context import StoreContextMixin


def _validated(serializer_class, request) -> dict:
    serializer = serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


class _ResolveMixin:
    """Resolve supplier/warehouse/variant ids against the active (scoped) store."""

    def _supplier(self, supplier_id) -> Supplier:
        supplier = Supplier.objects.filter(store=self.store, id=supplier_id).first()
        if supplier is None:
            raise ValidationError(
                "Supplier not found in this store.",
                errors={"supplier_id": ["Not found in this store."]},
            )
        return supplier

    def _warehouse(self, warehouse_id) -> Warehouse:
        warehouse = Warehouse.objects.filter(store=self.store, id=warehouse_id).first()
        if warehouse is None:
            raise ValidationError(
                "Warehouse not found in this store.",
                errors={"warehouse_id": ["Not found in this store."]},
            )
        return warehouse

    def _variant(self, variant_id) -> ProductVariant:
        variant = ProductVariant.objects.filter(id=variant_id).first()
        if variant is None:
            raise ValidationError(
                "Variant not found in this store.",
                errors={"variant_id": ["Not found in this store."]},
            )
        return variant


# --- Suppliers -------------------------------------------------------------
class SupplierListCreateView(StoreContextMixin, BaseGenericAPIView, generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SupplierSerializer
    search_fields = ("name", "code", "email")
    filterset_fields = ("is_active",)

    def get_queryset(self):
        return Supplier.objects.all()

    def perform_create(self, serializer):
        self.require_write()
        serializer.instance = ProcurementService().create_supplier(
            store=self.store, data=serializer.validated_data
        )


class SupplierDetailView(
    StoreContextMixin, BaseGenericAPIView, generics.RetrieveUpdateDestroyAPIView
):
    permission_classes = [IsAuthenticated]
    serializer_class = SupplierSerializer
    lookup_url_kwarg = "supplier_id"

    def get_queryset(self):
        return Supplier.objects.all()

    def perform_update(self, serializer):
        self.require_write()
        serializer.instance = ProcurementService().update_supplier(
            instance=serializer.instance, data=serializer.validated_data
        )

    def perform_destroy(self, instance):
        self.require_write()
        instance.delete()


# --- Purchase orders -------------------------------------------------------
class PurchaseOrderListCreateView(
    _ResolveMixin, StoreContextMixin, BaseGenericAPIView, generics.ListAPIView
):
    permission_classes = [IsAuthenticated]
    serializer_class = PurchaseOrderSerializer
    filterset_fields = ("status", "supplier", "warehouse")

    def get_queryset(self):
        return (
            PurchaseOrder.objects.select_related("supplier", "warehouse")
            .prefetch_related("lines")
            .all()
        )

    def post(self, request: Request, *args, **kwargs) -> Response:
        self.require_write()
        data = _validated(CreatePurchaseOrderSerializer, request)
        lines = [
            {
                "variant": self._variant(line["variant_id"]),
                "quantity_ordered": line["quantity_ordered"],
                "unit_cost": line["unit_cost"],
                "batch_number": line.get("batch_number", ""),
                "expiry_date": line.get("expiry_date"),
            }
            for line in data["lines"]
        ]
        po = ProcurementService().create_po(
            store=self.store,
            supplier=self._supplier(data["supplier_id"]),
            warehouse=self._warehouse(data["warehouse_id"]),
            lines=lines,
            expected_date=data.get("expected_date"),
            notes=data["notes"],
        )
        return APIResponse.success(
            PurchaseOrderSerializer(po).data, message="Purchase order created.", status_code=201
        )


class PurchaseOrderDetailView(StoreContextMixin, BaseGenericAPIView, generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PurchaseOrderSerializer
    lookup_url_kwarg = "po_id"

    def get_queryset(self):
        return PurchaseOrder.objects.select_related("supplier", "warehouse").prefetch_related(
            "lines"
        )


class _POActionView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]
    action = ""
    message = ""

    def post(self, request: Request, po_id) -> Response:
        self.require_write()
        po = ProcurementService.get_po(store=self.store, po_id=po_id)
        po = getattr(ProcurementService(), self.action)(po=po)
        return APIResponse.success(PurchaseOrderSerializer(po).data, message=self.message)


class PurchaseOrderSubmitView(_POActionView):
    action = "submit_po"
    message = "Purchase order submitted."


class PurchaseOrderCancelView(_POActionView):
    action = "cancel_po"
    message = "Purchase order cancelled."


class PurchaseOrderReceiveView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, po_id) -> Response:
        self.require_write()
        po = ProcurementService.get_po(store=self.store, po_id=po_id)
        data = _validated(ReceivePurchaseOrderSerializer, request)
        receipts = None
        if data.get("lines"):
            receipts = {str(line["line_id"]): line["quantity"] for line in data["lines"]}
        po = ProcurementService().receive_po(po=po, receipts=receipts)
        return APIResponse.success(PurchaseOrderSerializer(po).data, message="Stock received.")


# --- Batches / expiry ------------------------------------------------------
class StockBatchListView(StoreContextMixin, BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StockBatchSerializer
    filterset_fields = ("variant", "warehouse")

    def get_queryset(self):
        queryset = StockBatch.objects.all()
        before = self.request.query_params.get("expiring_before")
        if before:
            queryset = queryset.filter(
                quantity__gt=0, expiry_date__isnull=False, expiry_date__lte=before
            )
        return queryset


# --- Serial numbers --------------------------------------------------------
class SerialNumberListCreateView(
    _ResolveMixin, StoreContextMixin, BaseGenericAPIView, generics.ListAPIView
):
    permission_classes = [IsAuthenticated]
    serializer_class = SerialNumberSerializer
    filterset_fields = ("variant", "warehouse", "status")

    def get_queryset(self):
        return SerialNumber.objects.all()

    def post(self, request: Request, *args, **kwargs) -> Response:
        self.require_write()
        data = _validated(RegisterSerialsSerializer, request)
        batch = None
        if data.get("batch_id"):
            batch = StockBatch.objects.filter(store=self.store, id=data["batch_id"]).first()
        serials = ProcurementService().register_serials(
            store=self.store,
            variant=self._variant(data["variant_id"]),
            warehouse=self._warehouse(data["warehouse_id"]),
            serials=data["serials"],
            batch=batch,
        )
        return APIResponse.success(
            SerialNumberSerializer(serials, many=True).data,
            message="Serial numbers registered.",
            status_code=201,
        )


class SerialNumberDetailView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request, serial_id) -> Response:
        self.require_write()
        serial = SerialNumber.objects.filter(store=self.store, id=serial_id).first()
        if serial is None:
            raise NotFoundError("Serial number not found.")
        data = _validated(UpdateSerialStatusSerializer, request)
        serial = ProcurementService().set_serial_status(serial=serial, status=data["status"])
        return APIResponse.success(SerialNumberSerializer(serial).data, message="Serial updated.")


# --- Manufacturing: bills of materials -------------------------------------
class BillOfMaterialsListCreateView(
    _ResolveMixin, StoreContextMixin, BaseGenericAPIView, generics.ListAPIView
):
    permission_classes = [IsAuthenticated]
    serializer_class = BillOfMaterialsSerializer
    filterset_fields = ("is_active", "output_variant")

    def get_queryset(self):
        return BillOfMaterials.objects.prefetch_related("components").all()

    def post(self, request: Request, *args, **kwargs) -> Response:
        self.require_write()
        data = _validated(CreateBOMSerializer, request)
        bom = ManufacturingService().create_bom(
            store=self.store,
            output_variant=self._variant(data["output_variant_id"]),
            name=data["name"],
        )
        return APIResponse.success(
            BillOfMaterialsSerializer(bom).data,
            message="Bill of materials created.",
            status_code=201,
        )


class BillOfMaterialsDetailView(StoreContextMixin, BaseGenericAPIView, generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BillOfMaterialsSerializer
    lookup_url_kwarg = "bom_id"

    def get_queryset(self):
        return BillOfMaterials.objects.prefetch_related("components")


class BOMComponentListCreateView(_ResolveMixin, StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def _bom(self) -> BillOfMaterials:
        return ManufacturingService().get_bom(store=self.store, bom_id=self.kwargs["bom_id"])

    def get(self, request: Request, bom_id) -> Response:
        components = self._bom().components.all()
        return APIResponse.success(BOMComponentSerializer(components, many=True).data)

    def post(self, request: Request, bom_id) -> Response:
        self.require_write()
        data = _validated(AddBOMComponentSerializer, request)
        component = ManufacturingService().add_component(
            store=self.store,
            bom=self._bom(),
            component_variant=self._variant(data["component_variant_id"]),
            quantity=data["quantity"],
        )
        return APIResponse.success(
            BOMComponentSerializer(component).data, message="Component added.", status_code=201
        )


# --- Manufacturing: work orders --------------------------------------------
class WorkOrderListCreateView(
    _ResolveMixin, StoreContextMixin, BaseGenericAPIView, generics.ListAPIView
):
    permission_classes = [IsAuthenticated]
    serializer_class = WorkOrderSerializer
    filterset_fields = ("status", "bom", "warehouse")

    def get_queryset(self):
        return WorkOrder.objects.all()

    def post(self, request: Request, *args, **kwargs) -> Response:
        self.require_write()
        data = _validated(CreateWorkOrderSerializer, request)
        work_order = ManufacturingService().create_work_order(
            store=self.store,
            bom=ManufacturingService().get_bom(store=self.store, bom_id=data["bom_id"]),
            warehouse=self._warehouse(data["warehouse_id"]),
            quantity=data["quantity"],
        )
        return APIResponse.success(
            WorkOrderSerializer(work_order).data, message="Work order created.", status_code=201
        )


class WorkOrderDetailView(StoreContextMixin, BaseGenericAPIView, generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WorkOrderSerializer
    lookup_url_kwarg = "work_order_id"

    def get_queryset(self):
        return WorkOrder.objects.all()


class _WorkOrderActionView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]
    action = ""
    message = ""

    def post(self, request: Request, work_order_id) -> Response:
        self.require_write()
        work_order = ManufacturingService().get_work_order(
            store=self.store, work_order_id=work_order_id
        )
        work_order = getattr(ManufacturingService(), self.action)(work_order=work_order)
        return APIResponse.success(WorkOrderSerializer(work_order).data, message=self.message)


class WorkOrderCompleteView(_WorkOrderActionView):
    action = "complete_work_order"
    message = "Work order completed."


class WorkOrderCancelView(_WorkOrderActionView):
    action = "cancel_work_order"
    message = "Work order cancelled."
