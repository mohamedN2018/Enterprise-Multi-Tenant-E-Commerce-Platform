"""Returns API routes (mounted under /api/v1/returns/). Store via header."""

from django.urls import path

from apps.returns import views

app_name = "returns"

urlpatterns = [
    # Buyer
    path("", views.ReturnListCreateView.as_view(), name="list"),
    path("<uuid:return_id>/", views.ReturnDetailView.as_view(), name="detail"),
    path("<uuid:return_id>/cancel/", views.ReturnCancelView.as_view(), name="cancel"),
    # Staff
    path("manage/", views.ReturnManageListView.as_view(), name="manage"),
    path("<uuid:return_id>/approve/", views.ReturnApproveView.as_view(), name="approve"),
    path("<uuid:return_id>/reject/", views.ReturnRejectView.as_view(), name="reject"),
    path("<uuid:return_id>/refund/", views.ReturnRefundView.as_view(), name="refund"),
]
