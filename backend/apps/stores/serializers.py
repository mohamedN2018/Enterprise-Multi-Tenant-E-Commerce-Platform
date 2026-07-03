"""Serializers for the stores API."""

from __future__ import annotations

from rest_framework import serializers

from apps.accounts.models import User
from apps.stores.models import Store, StoreMembership, StoreSettings, StoreStatus


# --- Store -----------------------------------------------------------------
class StoreSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)

    class Meta:
        model = Store
        fields = (
            "id",
            "name",
            "slug",
            "owner",
            "owner_email",
            "status",
            "description",
            "email",
            "phone",
            "logo",
            "banner",
            "is_verified",
            "currency",
            "language",
            "timezone",
            "country",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "slug",
            "owner",
            "owner_email",
            "is_verified",
            "created_at",
            "updated_at",
        )


class StoreCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    phone = serializers.CharField(required=False, allow_blank=True, default="", max_length=32)
    currency = serializers.CharField(required=False, default="USD", max_length=3)
    language = serializers.CharField(required=False, default="en", max_length=10)
    timezone = serializers.CharField(required=False, default="UTC", max_length=64)
    country = serializers.CharField(required=False, allow_blank=True, default="", max_length=2)


class StoreUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = (
            "name",
            "description",
            "status",
            "email",
            "phone",
            "logo",
            "banner",
            "currency",
            "language",
            "timezone",
            "country",
        )
        extra_kwargs = {field: {"required": False} for field in fields}


# --- Settings --------------------------------------------------------------
class StoreSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreSettings
        fields = (
            "tax_inclusive_pricing",
            "default_tax_rate",
            "track_inventory",
            "allow_backorder",
            "low_stock_threshold",
            "weight_unit",
            "dimension_unit",
            "order_number_prefix",
            # Read-only for the seller: the employee cap is set by a platform admin.
            "max_employees",
            "metadata",
        )
        read_only_fields = ("max_employees",)


# --- Membership ------------------------------------------------------------
class MembershipSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = StoreMembership
        fields = (
            "id",
            "user",
            "user_email",
            "role",
            "is_active",
            "invited_by",
            "created_at",
        )
        read_only_fields = fields


class MembershipCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.CharField(max_length=16)


class MembershipUpdateSerializer(serializers.Serializer):
    role = serializers.CharField(max_length=16)


# --- Platform (super-admin) -------------------------------------------------
class PlatformStoreSerializer(serializers.ModelSerializer):
    """A store as seen by the platform admin: owner + team-size context."""

    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    owner_id = serializers.UUIDField(source="owner.id", read_only=True)
    owner_max_stores = serializers.IntegerField(source="owner.max_stores", read_only=True)
    max_employees = serializers.IntegerField(source="settings.max_employees", read_only=True)
    # Annotated in the view.
    member_count = serializers.IntegerField(read_only=True, default=0)
    employee_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Store
        fields = (
            "id",
            "name",
            "slug",
            "status",
            "owner_id",
            "owner_email",
            "owner_max_stores",
            "max_employees",
            "member_count",
            "employee_count",
            "currency",
            "country",
            "is_verified",
            "created_at",
        )
        read_only_fields = fields


class PlatformStoreCreateSerializer(serializers.Serializer):
    """Admin creates a store on behalf of a contracted seller (by email)."""

    owner_email = serializers.EmailField()
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    currency = serializers.CharField(required=False, default="USD", max_length=3)
    country = serializers.CharField(required=False, allow_blank=True, default="", max_length=2)
    status = serializers.ChoiceField(
        choices=StoreStatus.choices, required=False, default=StoreStatus.ACTIVE
    )


class PlatformStoreUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=StoreStatus.choices, required=False)
    is_verified = serializers.BooleanField(required=False)
    max_employees = serializers.IntegerField(required=False, min_value=0)


class SellerSerializer(serializers.ModelSerializer):
    store_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = User
        fields = ("id", "email", "is_active", "max_stores", "store_count", "created_at")
        read_only_fields = fields


class SellerUpdateSerializer(serializers.Serializer):
    max_stores = serializers.IntegerField(min_value=1)
