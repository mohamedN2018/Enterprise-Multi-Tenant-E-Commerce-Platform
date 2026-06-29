"""Celery tasks for procurement (scheduled background jobs)."""

from __future__ import annotations

from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.analytics.services import AnalyticsService
from apps.procurement.models import StockBatch


@shared_task(name="procurement.scan_expiring_batches")
def scan_expiring_batches(days: int = 7) -> int:
    """Record an analytics event for each in-stock lot expiring within ``days``.

    Runs across all stores; each event is attributed to the lot's store, giving
    operators a feed of soon-to-expire inventory. Returns the number flagged.
    """
    cutoff = (timezone.now() + timedelta(days=days)).date()
    batches = StockBatch.all_objects.filter(
        is_deleted=False, quantity__gt=0, expiry_date__isnull=False, expiry_date__lte=cutoff
    ).select_related("variant")
    analytics = AnalyticsService()
    flagged = 0
    for batch in batches:
        analytics.record(
            store=batch.store,
            event_type="inventory.batch_expiring",
            data={
                "batch_id": str(batch.id),
                "batch_number": batch.batch_number,
                "variant_id": str(batch.variant_id),
                "quantity": batch.quantity,
                "expiry_date": batch.expiry_date.isoformat(),
            },
        )
        flagged += 1
    return flagged
