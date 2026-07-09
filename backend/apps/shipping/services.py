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
    def _zones_for(self, *, store, country=None, lat=None, lng=None) -> list[ShippingZone]:
        """Zones that serve a destination. A geo (map) zone matches when the buyer's
        pinned location falls inside its circle; a country zone matches by country.
        Falls back to the store's default zone(s) as a nationwide catch-all — so a
        store that defines ONLY geo circles (no default) restricts delivery to them.
        """
        zones = list(ShippingZone.objects.filter(store=store))
        matched = []
        if lat is not None and lng is not None:
            matched += [z for z in zones if z.is_geo and z.covers_point(lat, lng)]
        if country:
            matched += [z for z in zones if not z.is_geo and z.covers(country)]
        if matched:
            # Preserve order but drop dups.
            seen, unique = set(), []
            for z in matched:
                if z.pk not in seen:
                    seen.add(z.pk)
                    unique.append(z)
            return unique
        return [z for z in zones if z.is_default]

    def _has_geo_zones(self, *, store) -> bool:
        return ShippingZone.objects.filter(
            store=store, radius_km__isnull=False, center_lat__isnull=False, center_lng__isnull=False
        ).exists()

    def available_methods(self, *, store, country=None, lat=None, lng=None):
        zones = self._zones_for(store=store, country=country, lat=lat, lng=lng)
        return ShippingMethod.objects.filter(zone__in=zones, is_active=True)

    def is_deliverable(self, *, store, country=None, lat=None, lng=None) -> bool:
        """Can this store deliver to the destination at all? True when it has no geo
        restriction, or the location falls inside a serviceable zone."""
        if not self._has_geo_zones(store=store):
            return True
        return bool(self._zones_for(store=store, country=country, lat=lat, lng=lng))

    def assert_deliverable(self, *, store, country=None, lat=None, lng=None) -> None:
        """Guard checkout: a store that restricts delivery to map zones must have the
        destination inside one of them (or a default zone), else the order is refused."""
        if not self.is_deliverable(store=store, country=country, lat=lat, lng=lng):
            raise BusinessRuleError(
                "Delivery isn't available at your location for this store.",
                code="delivery_unavailable",
            )

    def compute(self, *, store, method_id, country=None, subtotal: Decimal = Decimal("0"), weight=0, lat=None, lng=None):
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
        serves = (
            zone.is_default
            or (zone.is_geo and zone.covers_point(lat, lng))
            or (not zone.is_geo and zone.covers(country))
        )
        if not serves:
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
