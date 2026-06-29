"""Celery tasks for inventory (scheduled background jobs)."""

from __future__ import annotations

from celery import shared_task
from django.utils import timezone

from apps.inventory.models import ReservationStatus, StockReservation
from apps.inventory.services import InventoryService


@shared_task(name="inventory.expire_stale_reservations")
def expire_stale_reservations() -> int:
    """Release active reservations whose hold has expired, freeing the stock.

    Runs across all stores (no tenant context); each release is row-locked and
    ledgered by :class:`InventoryService`. Returns the number released.
    """
    now = timezone.now()
    stale = StockReservation.all_objects.filter(
        status=ReservationStatus.ACTIVE,
        is_deleted=False,
        expires_at__isnull=False,
        expires_at__lt=now,
    )
    service = InventoryService()
    released = 0
    for reservation in stale:
        service.release(reservation=reservation)
        released += 1
    return released
