"""Serializers for the accounts/auth API."""

from __future__ import annotations

from django.contrib.auth.password_validation import validate_password as dj_validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.accounts.models import User, UserDevice


# --- Output ----------------------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    # True when the user may reach the seller/admin console: a super-admin, a
    # store owner, or an active member of a store. Plain customers get False,
    # so the frontend hides the dashboard entirely for them.
    is_seller = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "is_active",
            "is_staff",
            "is_superuser",
            "is_verified",
            "is_seller",
            "two_factor_enabled",
            "max_stores",
            "last_login",
            "created_at",
        )
        read_only_fields = fields

    def get_is_seller(self, obj) -> bool:
        if obj.is_superuser:
            return True
        from apps.stores.models import Store, StoreMembership

        if StoreMembership.objects.filter(user=obj, is_active=True).exists():
            return True
        return Store.objects.filter(owner=obj).exists()


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDevice
        fields = (
            "id",
            "device_name",
            "user_agent",
            "ip_address",
            "last_used_at",
            "is_active",
            "created_at",
        )
        read_only_fields = fields


class TokenPairSerializer(serializers.Serializer):
    """Documents the token payload returned by login/refresh."""

    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)


# --- Input -----------------------------------------------------------------
def _validate_strength(value: str) -> str:
    try:
        dj_validate_password(value)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(list(exc.messages)) from exc
    return value


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_password(self, value: str) -> str:
        return _validate_strength(value)

    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs


class EmailVerifySerializer(serializers.Serializer):
    token = serializers.CharField()


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    remember_me = serializers.BooleanField(required=False, default=False)


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_new_password(self, value: str) -> str:
        return _validate_strength(value)

    def validate(self, attrs: dict) -> dict:
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_new_password(self, value: str) -> str:
        return _validate_strength(value)

    def validate(self, attrs: dict) -> dict:
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        return attrs
