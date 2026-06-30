"""Auth API routes (mounted under /api/v1/auth/)."""

from django.urls import path

from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    # Registration & email verification
    path("register/", views.RegisterView.as_view(), name="register"),
    path("verify-email/", views.VerifyEmailView.as_view(), name="verify-email"),
    path(
        "resend-verification/", views.ResendVerificationView.as_view(), name="resend-verification"
    ),
    # Session lifecycle
    path("login/", views.LoginView.as_view(), name="login"),
    path("token/refresh/", views.RefreshView.as_view(), name="token-refresh"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    # Password management
    path("password/reset/", views.PasswordResetRequestView.as_view(), name="password-reset"),
    path(
        "password/reset/confirm/",
        views.PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path("password/change/", views.PasswordChangeView.as_view(), name="password-change"),
    # Profile & devices
    path("me/", views.MeView.as_view(), name="me"),
    path("devices/", views.DeviceListView.as_view(), name="device-list"),
    path("devices/revoke-all/", views.DeviceRevokeAllView.as_view(), name="device-revoke-all"),
    path("devices/<uuid:device_id>/", views.DeviceRevokeView.as_view(), name="device-revoke"),
]
