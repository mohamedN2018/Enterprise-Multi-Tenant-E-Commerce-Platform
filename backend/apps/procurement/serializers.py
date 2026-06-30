"""Procurement serializers."""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.procurement.models import (
    BillOfMaterials,
    BOMComponent,
    PurchaseOrder,
    PurchaseOrderLine,
    SerialNumber,
    StockBatch,
    Supplier,
    WorkOrder,
)

_ZERO = Decimal("0")


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = (
            "id",
            "name",
            "code",
            "email",
            "phone",
            "address",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
        extra_kwargs = {"code": {"required": False}}


class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    quantity_outstanding = serializers.IntegerField(read_only=True)

    class Meta:
        model = PurchaseOrderLine
        fields = (
            "id",
            "variant",
            "quantity_ordered",
            "quantity_received",
            "quantity_outstanding",
            "unit_cost",
            "line_total",
            "batch_number",
            "expiry_date",
        )
        read_only_fields = fields


class PurchaseOrderSerializer(serializers.ModelSerializer):
    lines = PurchaseOrderLineSerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = (
            "id",
            "number",
            "supplier",
            "warehouse",
            "status",
            "expected_date",
            "notes",
            "subtotal",
            "received_at",
            "lines",
            "created_at",
        )
        read_only_fields = fields


class POLineInputSerializer(serializers.Serializer):
    variant_id = serializers.UUIDField()
    quantity_ordered = serializers.IntegerField(min_value=1)
    unit_cost = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=_ZERO, required=False, default=_ZERO
    )
    batch_number = serializers.CharField(
        max_length=60, required=False, allow_blank=True, default=""
    )
    expiry_date = serializers.DateField(required=False, allow_null=True)


class CreatePurchaseOrderSerializer(serializers.Serializer):
    supplier_id = serializers.UUIDField()
    warehouse_id = serializers.UUIDField()
    expected_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    lines = POLineInputSerializer(many=True)

    def validate_lines(self, value):
        if not value:
            raise serializers.ValidationError("At least one line is required.")
        return value


class ReceiptLineSerializer(serializers.Serializer):
    line_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


class ReceivePurchaseOrderSerializer(serializers.Serializer):
    lines = ReceiptLineSerializer(many=True, required=False)


class StockBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockBatch
        fields = (
            "id",
            "variant",
            "warehouse",
            "batch_number",
            "quantity",
            "expiry_date",
            "purchase_order",
            "created_at",
        )
        read_only_fields = fields


class SerialNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = SerialNumber
        fields = ("id", "variant", "warehouse", "serial", "status", "batch", "created_at")
        read_only_fields = ("id", "variant", "warehouse", "serial", "batch", "created_at")


class RegisterSerialsSerializer(serializers.Serializer):
    variant_id = serializers.UUIDField()
    warehouse_id = serializers.UUIDField()
    serials = serializers.ListField(child=serializers.CharField(max_length=120), allow_empty=False)
    batch_id = serializers.UUIDField(required=False, allow_null=True)


class UpdateSerialStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=SerialNumber._meta.get_field("status").choices)


# --- Manufacturing -------------------------------------------------------
class BOMComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BOMComponent
        fields = ("id", "component_variant", "quantity", "created_at")
        read_only_fields = fields


class BillOfMaterialsSerializer(serializers.ModelSerializer):
    components = BOMComponentSerializer(many=True, read_only=True)

    class Meta:
        model = BillOfMaterials
        fields = ("id", "output_variant", "name", "is_active", "components", "created_at")
        read_only_fields = fields


class CreateBOMSerializer(serializers.Serializer):
    output_variant_id = serializers.UUIDField()
    name = serializers.CharField(max_length=150)


class AddBOMComponentSerializer(serializers.Serializer):
    component_variant_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


class WorkOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrder
        fields = (
            "id",
            "number",
            "bom",
            "warehouse",
            "quantity",
            "status",
            "completed_at",
            "created_at",
        )
        read_only_fields = fields


class CreateWorkOrderSerializer(serializers.Serializer):
    bom_id = serializers.UUIDField()
    warehouse_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
