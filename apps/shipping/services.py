"""Shipping application service: zones, methods, rate resolution, tracking."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from django.utils.text import slugify

from apps.core.exceptions import BusinessRuleError, ConflictError, NotFoundError, ValidationError
from apps.core.services import BaseService, atomic
from apps.shipping.models import ShippingMethod, ShippingZone

_CENTS = Decimal("0.01")


def _money(value) -> Decimal:
    return Decimal(value).quantize(_CENTS, rounding=ROUND_HALF_UP)


class ShippingService(BaseService):
    # --- Resolution / quoting ---
    def _zones_for(self, *, store, country: str | None) -> list[ShippingZone]:
        zones = list(ShippingZone.objects.filter(store=store))
        if country:
            matched = [z for z in zones if z.covers(country)]
            if matched:
                return matched
        return [z for z in zones if z.is_default]

    def available_methods(self, *, store, country: str | None):
        zones = self._zones_for(store=store, country=country)
        return ShippingMethod.objects.filter(zone__in=zones, is_active=True)

    def compute(self, *, store, method_id, country: str | None, subtotal: Decimal, weight):
        method = (
            ShippingMethod.objects.filter(id=method_id, is_active=True)
            .select_related("zone")
            .first()
        )
        if method is None:
            raise ValidationError(
                "Shipping method not available.",
                code="method_unavailable",
                errors={"shipping_method_id": ["Not available in this store."]},
            )
        zone = method.zone
        if not (zone.covers(country) or zone.is_default):
            raise BusinessRuleError(
                "This shipping method does not serve the destination.",
                code="method_not_serviceable",
            )
        return method, _money(method.quote(subtotal=subtotal, weight=weight))

    # --- Zone management ---
    @atomic
    def create_zone(self, *, store, data: dict) -> ShippingZone:
        code = data.get("code")
        if code:
            if ShippingZone.all_objects.filter(store=store, code=code, is_deleted=False).exists():
                raise ConflictError("A zone with this code already exists.", code="code_taken")
        else:
            code = self._unique_code(store=store, name=data["name"])
        payload = {k: v for k, v in data.items() if k != "code"}
        zone = ShippingZone.objects.create(store=store, code=code, **payload)
        if zone.is_default:
            ShippingZone.objects.filter(store=store, is_default=True).exclude(pk=zone.pk).update(
                is_default=False
            )
        return zone

    @atomic
    def update_zone(self, *, instance: ShippingZone, data: dict) -> ShippingZone:
        for field, value in data.items():
            setattr(instance, field, value)
        instance.save()
        if instance.is_default:
            ShippingZone.objects.filter(store=instance.store, is_default=True).exclude(
                pk=instance.pk
            ).update(is_default=False)
        return instance

    def get_zone(self, *, zone_id) -> ShippingZone:
        zone = ShippingZone.objects.filter(id=zone_id).first()
        if zone is None:
            raise NotFoundError("Shipping zone not found.")
        return zone

    # --- Method management ---
    def list_methods(self, zone: ShippingZone):
        return zone.methods.all()

    @atomic
    def add_method(self, *, store, zone: ShippingZone, data: dict) -> ShippingMethod:
        return ShippingMethod.objects.create(store=store, zone=zone, **data)

    # --- Tracking ---
    @atomic
    def set_tracking(self, *, order, tracking_number: str):
        order.tracking_number = tracking_number
        order.save(update_fields=["tracking_number", "updated_at"])
        return order

    def _unique_code(self, *, store, name: str) -> str:
        base = slugify(name)[:110] or "zone"
        code = base
        suffix = 1
        while ShippingZone.all_objects.filter(store=store, code=code, is_deleted=False).exists():
            suffix += 1
            code = f"{base}-{suffix}"
        return code
