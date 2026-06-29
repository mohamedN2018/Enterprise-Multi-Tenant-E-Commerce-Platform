"""Pricing API routes (mounted under /api/v1/pricing/). Store via header."""

from django.urls import path

from apps.pricing import views

app_name = "pricing"

urlpatterns = [
    # Customer groups
    path("groups/", views.CustomerGroupListCreateView.as_view(), name="group-list"),
    path("groups/<uuid:group_id>/", views.CustomerGroupDetailView.as_view(), name="group-detail"),
    path(
        "groups/<uuid:group_id>/members/",
        views.GroupMemberListCreateView.as_view(),
        name="group-members",
    ),
    path(
        "groups/<uuid:group_id>/members/<uuid:user_id>/",
        views.GroupMemberDetailView.as_view(),
        name="group-member-detail",
    ),
    # Price rules
    path("rules/", views.PriceRuleListCreateView.as_view(), name="rule-list"),
    path("rules/<uuid:rule_id>/", views.PriceRuleDetailView.as_view(), name="rule-detail"),
    # Buyer quote
    path("quote/", views.PriceQuoteView.as_view(), name="quote"),
]
