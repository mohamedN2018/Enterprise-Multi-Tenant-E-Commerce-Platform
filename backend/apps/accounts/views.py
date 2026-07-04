"""Authentication API views.

Thin HTTP layer: validate input (serializers) -> delegate to services ->
return the standard response envelope. All business rules live in services.
"""

from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts import serializers as s
from apps.accounts.serializers import DeviceSerializer, UserSerializer
from apps.accounts.services import (
    AuthenticationService,
    DeviceService,
    EmailVerificationService,
    PasswordService,
    RegistrationService,
)
from apps.accounts.utils import extract_request_meta
from apps.core.mixins import BaseAPIView, BaseGenericAPIView
from apps.core.responses import APIResponse

_GENERIC_EMAIL_MSG = "If an account matches the information provided, an email has been sent."


# --- Registration & verification ------------------------------------------
class RegisterView(BaseAPIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "auth_register"
    serializer_class = s.RegisterSerializer

    # Identical for a new or an already-registered email — no user data, so the
    # response can't be used to enumerate which addresses have accounts.
    _MESSAGE = (
        "Thanks — if this email is available, we've sent a verification link. "
        "Check your inbox to finish setting up your account."
    )

    @extend_schema(request=s.RegisterSerializer, responses={202: None}, tags=["auth"])
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        RegistrationService().register(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            meta=extract_request_meta(request),
        )
        return APIResponse.success(
            message=self._MESSAGE,
            status_code=status.HTTP_202_ACCEPTED,
        )


class VerifyEmailView(BaseAPIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "auth_email_verification"
    serializer_class = s.EmailVerifySerializer

    @extend_schema(request=s.EmailVerifySerializer, responses={200: UserSerializer}, tags=["auth"])
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = EmailVerificationService().verify(
            raw_token=serializer.validated_data["token"],
            meta=extract_request_meta(request),
        )
        return APIResponse.success(
            data=UserSerializer(user).data, message="Email verified successfully."
        )


class ResendVerificationView(BaseAPIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "auth_email_verification"
    serializer_class = s.ResendVerificationSerializer

    @extend_schema(
        request=s.ResendVerificationSerializer, responses={200: OpenApiResponse()}, tags=["auth"]
    )
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        EmailVerificationService().resend(email=serializer.validated_data["email"])
        return APIResponse.success(message=_GENERIC_EMAIL_MSG)


# --- Session lifecycle -----------------------------------------------------
class LoginView(BaseAPIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "auth_login"
    serializer_class = s.LoginSerializer

    @extend_schema(request=s.LoginSerializer, responses={200: s.TokenPairSerializer}, tags=["auth"])
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = AuthenticationService().login(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            remember_me=serializer.validated_data["remember_me"],
            meta=extract_request_meta(request),
        )
        return APIResponse.success(
            data={
                "user": UserSerializer(result["user"]).data,
                "tokens": {"access": result["access"], "refresh": result["refresh"]},
            },
            message="Login successful.",
        )


class RefreshView(BaseAPIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []
    serializer_class = s.RefreshSerializer

    @extend_schema(
        request=s.RefreshSerializer, responses={200: s.TokenPairSerializer}, tags=["auth"]
    )
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = AuthenticationService().refresh(
            raw_refresh=serializer.validated_data["refresh"],
            meta=extract_request_meta(request),
        )
        return APIResponse.success(data=tokens, message="Token refreshed.")


class LogoutView(BaseAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = s.LogoutSerializer

    @extend_schema(request=s.LogoutSerializer, responses={200: OpenApiResponse()}, tags=["auth"])
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthenticationService().logout(
            raw_refresh=serializer.validated_data["refresh"],
            user=request.user,
            meta=extract_request_meta(request),
        )
        return APIResponse.success(message="Logged out successfully.")


# --- Password management ---------------------------------------------------
class PasswordResetRequestView(BaseAPIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "auth_password_reset"
    serializer_class = s.PasswordResetRequestSerializer

    @extend_schema(
        request=s.PasswordResetRequestSerializer, responses={200: OpenApiResponse()}, tags=["auth"]
    )
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        PasswordService().request_reset(
            email=serializer.validated_data["email"],
            meta=extract_request_meta(request),
        )
        return APIResponse.success(message=_GENERIC_EMAIL_MSG)


class PasswordResetConfirmView(BaseAPIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_scope = "auth_password_reset"
    serializer_class = s.PasswordResetConfirmSerializer

    @extend_schema(
        request=s.PasswordResetConfirmSerializer, responses={200: OpenApiResponse()}, tags=["auth"]
    )
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        PasswordService().confirm_reset(
            raw_token=serializer.validated_data["token"],
            new_password=serializer.validated_data["new_password"],
            meta=extract_request_meta(request),
        )
        return APIResponse.success(message="Password reset successful. You can now sign in.")


class PasswordChangeView(BaseAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = s.PasswordChangeSerializer

    @extend_schema(
        request=s.PasswordChangeSerializer, responses={200: OpenApiResponse()}, tags=["auth"]
    )
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        PasswordService().change_password(
            user=request.user,
            current_password=serializer.validated_data["current_password"],
            new_password=serializer.validated_data["new_password"],
            meta=extract_request_meta(request),
        )
        return APIResponse.success(
            message="Password changed. Please sign in again on your devices."
        )


# --- Profile & devices -----------------------------------------------------
class MeView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: UserSerializer}, tags=["auth"])
    def get(self, request: Request) -> Response:
        return APIResponse.success(data=UserSerializer(request.user).data)


class DeviceListView(BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DeviceSerializer

    def get_queryset(self):
        return DeviceService().list_active(self.request.user)

    @extend_schema(responses={200: DeviceSerializer(many=True)}, tags=["auth"])
    def get(self, request: Request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)


class DeviceRevokeView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: OpenApiResponse()}, tags=["auth"])
    def delete(self, request: Request, device_id) -> Response:
        DeviceService().revoke(
            user=request.user, device_id=device_id, meta=extract_request_meta(request)
        )
        return APIResponse.success(message="Device revoked.")


class DeviceRevokeAllView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: OpenApiResponse()}, tags=["auth"])
    def post(self, request: Request) -> Response:
        count = DeviceService().revoke_all(user=request.user, meta=extract_request_meta(request))
        return APIResponse.success(data={"revoked": count}, message="All sessions revoked.")
