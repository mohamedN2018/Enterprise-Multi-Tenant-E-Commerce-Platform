"""Address application service: per-store address book with a single default."""

from __future__ import annotations

from apps.addresses.models import Address
from apps.core.exceptions import NotFoundError
from apps.core.services import BaseService, atomic


class AddressService(BaseService):
    @atomic
    def create_address(self, *, store, user, data: dict) -> Address:
        address = Address.objects.create(store=store, user=user, **data)
        self._enforce_single_default(store=store, user=user, address=address)
        return address

    @atomic
    def update_address(self, *, instance: Address, data: dict) -> Address:
        for field, value in data.items():
            setattr(instance, field, value)
        instance.save()
        self._enforce_single_default(store=instance.store, user=instance.user, address=instance)
        return instance

    def delete_address(self, *, address: Address) -> None:
        address.delete()

    @atomic
    def set_default(self, *, address: Address) -> Address:
        address.is_default = True
        address.save(update_fields=["is_default", "updated_at"])
        self._enforce_single_default(store=address.store, user=address.user, address=address)
        return address

    def get_for_user(self, *, store, user, address_id) -> Address:
        address = Address.objects.filter(store=store, user=user, id=address_id).first()
        if address is None:
            raise NotFoundError("Address not found.")
        return address

    @staticmethod
    def _enforce_single_default(*, store, user, address: Address) -> None:
        if address.is_default:
            Address.objects.filter(store=store, user=user, is_default=True).exclude(
                pk=address.pk
            ).update(is_default=False)
