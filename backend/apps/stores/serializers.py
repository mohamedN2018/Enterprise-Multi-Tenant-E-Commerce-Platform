"""Serializers for the stores API."""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.accounts.models import User
from apps.stores.models import (
    LimitRequest,
    Store,
    StoreMembership,
    StoreSettings,
    StoreStatus,
)


# --- Store -----------------------------------------------------------------
class StoreSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)

    class Meta:
        model = Store
        fields = (
            "id",
            "name",
            "name_en",
            "slug",
            "owner",
            "owner_email",
            "status",
            "description",
            "description_en",
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
    name_en = serializers.CharField(required=False, allow_blank=True, default="", max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    phone = serializers.CharField(required=False, allow_blank=True, default="", max_length=32)
    currency = serializers.CharField(required=False, default="EGP", max_length=3)
    language = serializers.CharField(required=False, default="en", max_length=10)
    timezone = serializers.CharField(required=False, default="UTC", max_length=64)
    country = serializers.CharField(required=False, allow_blank=True, default="", max_length=2)


class StoreUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = (
            "name",
            "name_en",
            "description",
            "description_en",
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
        # A negative default tax rate would charge less than subtotal; the
        # threshold cannot be negative either.
        extra_kwargs = {
            "default_tax_rate": {"min_value": Decimal("0")},
            "low_stock_threshold": {"min_value": 0},
        }


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
            "permissions",
            "is_active",
            "invited_by",
            "created_at",
        )
        read_only_fields = fields


class _PermissionsField(serializers.ListField):
    """A list of valid permission-area keys (unknown/duplicate values dropped)."""

    child = serializers.CharField()

    def to_internal_value(self, data):
        from apps.stores.access import PERMISSION_AREAS

        values = super().to_internal_value(data)
        return [v for v in dict.fromkeys(values) if v in PERMISSION_AREAS]


class MembershipCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.CharField(max_length=16)
    permissions = _PermissionsField(required=False, default=list)


class MembershipUpdateSerializer(serializers.Serializer):
    role = serializers.CharField(max_length=16)
    permissions = _PermissionsField(required=False, default=list)


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
    product_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Store
        fields = (
            "id",
            "name",
            "slug",
            "status",
            "is_deleted",
            "deleted_at",
            "owner_id",
            "owner_email",
            "owner_max_stores",
            "max_employees",
            "member_count",
            "employee_count",
            "product_count",
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
    currency = serializers.CharField(required=False, default="EGP", max_length=3)
    country = serializers.CharField(required=False, allow_blank=True, default="", max_length=2)
    status = serializers.ChoiceField(
        choices=StoreStatus.choices, required=False, default=StoreStatus.ACTIVE
    )


class PlatformStoreUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=StoreStatus.choices, required=False)
    is_verified = serializers.BooleanField(required=False)
    max_employees = serializers.IntegerField(required=False, min_value=0)
    # Set false to restore a soft-deleted store (admin-only recovery).
    is_deleted = serializers.BooleanField(required=False)


class SellerSerializer(serializers.ModelSerializer):
    store_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = User
        fields = ("id", "email", "is_active", "max_stores", "store_count", "created_at")
        read_only_fields = fields


class PlatformSellerCreateSerializer(serializers.Serializer):
    """Admin creates a seller account. Each seller gets one store by default
    (``max_stores`` defaults to 1); optionally provision that first store now."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8, max_length=128)
    store_name = serializers.CharField(required=False, allow_blank=True, default="", max_length=255)
    country = serializers.CharField(required=False, allow_blank=True, default="", max_length=2)


class SellerUpdateSerializer(serializers.Serializer):
    max_stores = serializers.IntegerField(min_value=1)


class LimitRequestSerializer(serializers.ModelSerializer):
    requester_email = serializers.EmailField(source="requested_by.email", read_only=True)
    store_name = serializers.CharField(source="store.name", read_only=True, default=None)

    class Meta:
        model = LimitRequest
        fields = (
            "id",
            "kind",
            "current_limit",
            "requested_limit",
            "note",
            "status",
            "requester_email",
            "store_name",
            "created_at",
            "resolved_at",
        )
        read_only_fields = fields


class LimitRequestCreateSerializer(serializers.Serializer):
    requested_limit = serializers.IntegerField(min_value=1)
    note = serializers.CharField(required=False, allow_blank=True, default="", max_length=500)


# --- Platform branding / theme (super-admin) ---
import re as _re  # noqa: E402

_HEX_RE = _re.compile(r"^#[0-9a-fA-F]{6}$")
THEME_FONTS = ["Cairo", "Tajawal", "Almarai", "Roboto", "Open Sans"]
DEFAULT_THEME = {
    "preset": "sunset",
    "primary": "#F28B00",
    "secondary": "#F92400",
    "background": "#F5F5F5",
    "font": "Cairo",
    "heading_font": "Cairo",
}


class PlatformThemeSerializer(serializers.Serializer):
    """Validates a (partial) theme update. All fields optional so the admin can
    tweak one thing at a time; colors must be #RRGGBB, fonts from a known set."""

    preset = serializers.CharField(max_length=40, required=False, allow_blank=True)
    primary = serializers.RegexField(_HEX_RE, required=False)
    secondary = serializers.RegexField(_HEX_RE, required=False)
    background = serializers.RegexField(_HEX_RE, required=False)
    font = serializers.ChoiceField(choices=THEME_FONTS, required=False)
    heading_font = serializers.ChoiceField(choices=THEME_FONTS, required=False)
