"""Pricing API views (staff management + buyer price quote)."""

from __future__ import annotations

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.catalog.models import ProductVariant
from apps.core.exceptions import NotFoundError, ValidationError
from apps.core.mixins import BaseAPIView, BaseGenericAPIView
from apps.core.responses import APIResponse
from apps.pricing.models import CustomerGroup, PriceRule
from apps.pricing.serializers import (
    AssignMemberSerializer,
    CreatePriceRuleSerializer,
    CustomerGroupMembershipSerializer,
    CustomerGroupSerializer,
    PriceRuleSerializer,
    UpdatePriceRuleSerializer,
)
from apps.pricing.services import PricingService
from apps.stores.context import RequireStoreMixin, StoreContextMixin


# --- Customer groups (staff) -----------------------------------------------
class CustomerGroupListCreateView(
    StoreContextMixin, BaseGenericAPIView, generics.ListCreateAPIView
):
    permission_classes = [IsAuthenticated]
    serializer_class = CustomerGroupSerializer
    search_fields = ("name", "code")

    def get_queryset(self):
        return CustomerGroup.objects.all()

    def perform_create(self, serializer):
        self.require_write()
        serializer.instance = PricingService().create_group(
            store=self.store, data=serializer.validated_data
        )


class CustomerGroupDetailView(
    StoreContextMixin, BaseGenericAPIView, generics.RetrieveUpdateDestroyAPIView
):
    permission_classes = [IsAuthenticated]
    serializer_class = CustomerGroupSerializer
    lookup_url_kwarg = "group_id"

    def get_queryset(self):
        return CustomerGroup.objects.all()

    def perform_update(self, serializer):
        self.require_write()
        serializer.instance = PricingService().update_group(
            instance=serializer.instance, data=serializer.validated_data
        )

    def perform_destroy(self, instance):
        self.require_write()
        instance.delete()


class GroupMemberListCreateView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def _group(self, group_id) -> CustomerGroup:
        group = CustomerGroup.objects.filter(id=group_id).first()
        if group is None:
            raise NotFoundError("Customer group not found.")
        return group

    def get(self, request, group_id):
        group = self._group(group_id)
        members = PricingService().list_members(group)
        return APIResponse.success(CustomerGroupMembershipSerializer(members, many=True).data)

    def post(self, request, group_id):
        self.require_write()
        group = self._group(group_id)
        serializer = AssignMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = PricingService().assign_member(
            store=self.store, group=group, email=serializer.validated_data["email"]
        )
        return APIResponse.success(
            CustomerGroupMembershipSerializer(membership).data,
            message="Member assigned to group.",
            status_code=201,
        )


class GroupMemberDetailView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, group_id, user_id):
        self.require_write()
        group = CustomerGroup.objects.filter(id=group_id).first()
        if group is None:
            raise NotFoundError("Customer group not found.")
        PricingService().remove_member(group=group, user_id=user_id)
        return APIResponse.success(message="Member removed from group.")


# --- Price rules (staff) ---------------------------------------------------
class PriceRuleListCreateView(StoreContextMixin, BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PriceRuleSerializer
    filterset_fields = ("variant", "customer_group", "is_active")

    def get_queryset(self):
        return PriceRule.objects.all()

    def post(self, request: Request, *args, **kwargs) -> Response:
        self.require_write()
        serializer = CreatePriceRuleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rule = PricingService().create_rule(store=self.store, data=serializer.validated_data)
        return APIResponse.success(
            PriceRuleSerializer(rule).data, message="Price rule created.", status_code=201
        )


class PriceRuleDetailView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def _rule(self, rule_id) -> PriceRule:
        rule = PriceRule.objects.filter(id=rule_id).first()
        if rule is None:
            raise NotFoundError("Price rule not found.")
        return rule

    def get(self, request, rule_id):
        return APIResponse.success(PriceRuleSerializer(self._rule(rule_id)).data)

    def patch(self, request, rule_id):
        self.require_write()
        serializer = UpdatePriceRuleSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        rule = PricingService().update_rule(
            instance=self._rule(rule_id), data=serializer.validated_data
        )
        return APIResponse.success(PriceRuleSerializer(rule).data, message="Price rule updated.")

    def delete(self, request, rule_id):
        self.require_write()
        self._rule(rule_id).delete()
        return APIResponse.success(message="Price rule deleted.")


# --- Buyer price quote -----------------------------------------------------
class PriceQuoteView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        variant_id = request.query_params.get("variant")
        quantity = request.query_params.get("quantity", "1")
        if not variant_id:
            raise ValidationError(
                "A 'variant' query parameter is required.", code="variant_required"
            )
        try:
            quantity = max(int(quantity), 1)
        except (TypeError, ValueError):
            raise ValidationError(
                "'quantity' must be an integer.", code="invalid_quantity"
            ) from None

        variant = ProductVariant.objects.filter(id=variant_id).first()
        if variant is None:
            raise NotFoundError("Variant not found.")
        price = PricingService().resolve_price(
            store=self.store, variant=variant, user=request.user, quantity=quantity
        )
        return APIResponse.success(
            data={
                "variant": str(variant.id),
                "quantity": quantity,
                "base_price": str(variant.price),
                "unit_price": str(price),
            }
        )
