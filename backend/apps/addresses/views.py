"""Address API (buyer-facing): manage a per-store address book."""

from __future__ import annotations

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.addresses.models import Address
from apps.addresses.serializers import AddressSerializer
from apps.addresses.services import AddressService
from apps.core.mixins import BaseAPIView, BaseGenericAPIView
from apps.core.responses import APIResponse
from apps.stores.context import RequireStoreMixin


class AddressListCreateView(RequireStoreMixin, BaseGenericAPIView, generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer

    def get_queryset(self):
        return Address.objects.filter(store=self.store, user=self.request.user)

    def perform_create(self, serializer):
        serializer.instance = AddressService().create_address(
            store=self.store, user=self.request.user, data=serializer.validated_data
        )


class AddressDetailView(
    RequireStoreMixin, BaseGenericAPIView, generics.RetrieveUpdateDestroyAPIView
):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer
    lookup_url_kwarg = "address_id"

    def get_queryset(self):
        return Address.objects.filter(store=self.store, user=self.request.user)

    def perform_update(self, serializer):
        serializer.instance = AddressService().update_address(
            instance=serializer.instance, data=serializer.validated_data
        )

    def perform_destroy(self, instance):
        instance.delete()


class AddressSetDefaultView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, address_id) -> Response:
        service = AddressService()
        address = service.set_default(
            address=service.get_for_user(store=self.store, user=request.user, address_id=address_id)
        )
        return APIResponse.success(AddressSerializer(address).data, message="Default address set.")
