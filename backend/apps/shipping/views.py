"""Shipping API views: zones/methods (staff), tracking (staff), available methods (buyer)."""

from __future__ import annotations

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.core.exceptions import NotFoundError
from apps.core.mixins import BaseAPIView, BaseGenericAPIView
from apps.core.responses import APIResponse
from apps.orders.models import Order
from apps.shipping.models import ShippingZone
from apps.shipping.serializers import (
    AvailableMethodSerializer,
    SetTrackingSerializer,
    ShippingMethodSerializer,
    ShippingZoneSerializer,
)
from apps.shipping.services import ShippingService
from apps.stores.context import RequireStoreMixin, StoreContextMixin


# --- Zones & methods (staff) ----------------------------------------------
class ShippingZoneListCreateView(StoreContextMixin, BaseGenericAPIView, generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ShippingZoneSerializer

    def get_queryset(self):
        return ShippingZone.objects.all()

    def perform_create(self, serializer):
        self.require_write()
        serializer.instance = ShippingService().create_zone(
            store=self.store, data=serializer.validated_data
        )


class ShippingZoneDetailView(
    StoreContextMixin, BaseGenericAPIView, generics.RetrieveUpdateDestroyAPIView
):
    permission_classes = [IsAuthenticated]
    serializer_class = ShippingZoneSerializer
    lookup_url_kwarg = "zone_id"

    def get_queryset(self):
        return ShippingZone.objects.all()

    def perform_update(self, serializer):
        self.require_write()
        serializer.instance = ShippingService().update_zone(
            instance=serializer.instance, data=serializer.validated_data
        )

    def perform_destroy(self, instance):
        self.require_write()
        instance.delete()


class ShippingMethodListCreateView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, zone_id):
        zone = ShippingService().get_zone(zone_id=zone_id)
        return APIResponse.success(
            ShippingMethodSerializer(ShippingService().list_methods(zone), many=True).data
        )

    def post(self, request, zone_id):
        self.require_write()
        service = ShippingService()
        zone = service.get_zone(zone_id=zone_id)
        serializer = ShippingMethodSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        method = service.add_method(store=self.store, zone=zone, data=serializer.validated_data)
        return APIResponse.success(
            ShippingMethodSerializer(method).data, message="Shipping method added.", status_code=201
        )


class OrderTrackingView(StoreContextMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        self.require_write()
        order = Order.objects.filter(id=order_id).first()
        if order is None:
            raise NotFoundError("Order not found.")
        serializer = SetTrackingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ShippingService().set_tracking(
            order=order, tracking_number=serializer.validated_data["tracking_number"]
        )
        return APIResponse.success(
            data={"order": str(order.id), "tracking_number": order.tracking_number},
            message="Tracking number set.",
        )


# --- Available methods (buyer) --------------------------------------------
class AvailableMethodsView(RequireStoreMixin, BaseAPIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _coord(value):
        try:
            return float(value) if value not in (None, "") else None
        except (TypeError, ValueError):
            return None

    def get(self, request):
        country = request.query_params.get("country") or self.store.country or None
        lat = self._coord(request.query_params.get("lat"))
        lng = self._coord(request.query_params.get("lng"))
        service = ShippingService()
        methods = service.available_methods(store=self.store, country=country, lat=lat, lng=lng)
        # Whether this store can deliver to the location at all (drives the buyer's
        # "delivery not available in your area" message before they pay).
        deliverable = service.is_deliverable(store=self.store, country=country, lat=lat, lng=lng)
        # The store's delivery circles, so the checkout map can show coverage.
        geo_zones = [
            {
                "id": str(z.id),
                "name": z.name,
                "center_lat": float(z.center_lat),
                "center_lng": float(z.center_lng),
                "radius_km": float(z.radius_km),
            }
            for z in ShippingZone.objects.filter(
                store=self.store,
                radius_km__isnull=False,
                center_lat__isnull=False,
                center_lng__isnull=False,
            )
        ]
        return APIResponse.success(
            {
                "deliverable": deliverable,
                "methods": AvailableMethodSerializer(methods, many=True).data,
                "geo_zones": geo_zones,
            }
        )
