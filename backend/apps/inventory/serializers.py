"""Inventory serializers."""

from __future__ import annotations

from rest_framework import serializers

from apps.inventory.models import StockItem, StockMovement, Warehouse


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = (
            "id",
            "name",
            "code",
            "address",
            "city",
            "country",
            "is_default",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class StockItemSerializer(serializers.ModelSerializer):
    available_quantity = serializers.IntegerField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    is_out_of_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = StockItem
        fields = (
            "id",
            "variant",
            "warehouse",
            "quantity",
            "reserved_quantity",
            "available_quantity",
            "reorder_point",
            "is_low_stock",
            "is_out_of_stock",
            "updated_at",
        )
        read_only_fields = fields


class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = (
            "id",
            "variant",
            "warehouse",
            "movement_type",
            "quantity_change",
            "reserved_change",
            "resulting_quantity",
            "reference",
            "note",
            "created_at",
        )
        read_only_fields = fields


# --- Operation inputs (ids resolved against the active store in the view) ---
class ReceiveStockSerializer(serializers.Serializer):
    variant_id = serializers.UUIDField()
    warehouse_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    reference = serializers.CharField(required=False, allow_blank=True, default="")
    note = serializers.CharField(required=False, allow_blank=True, default="")


class AdjustStockSerializer(serializers.Serializer):
    variant_id = serializers.UUIDField()
    warehouse_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=0)
    note = serializers.CharField(required=False, allow_blank=True, default="")


class TransferStockSerializer(serializers.Serializer):
    variant_id = serializers.UUIDField()
    from_warehouse_id = serializers.UUIDField()
    to_warehouse_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    note = serializers.CharField(required=False, allow_blank=True, default="")
