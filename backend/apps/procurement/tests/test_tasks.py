"""Procurement scheduled-task tests (P2.10): expiring-batch scan."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from apps.analytics.models import AnalyticsEvent
from apps.procurement.models import StockBatch
from apps.procurement.tasks import scan_expiring_batches

pytestmark = pytest.mark.django_db


def test_scan_flags_soon_to_expire_batches(make_store, make_variant, make_warehouse):
    store, _owner = make_store()
    variant = make_variant(store)
    warehouse = make_warehouse(store)
    StockBatch.objects.create(
        store=store,
        variant=variant,
        warehouse=warehouse,
        batch_number="SOON",
        quantity=5,
        expiry_date=date.today() + timedelta(days=3),
    )
    StockBatch.objects.create(
        store=store,
        variant=variant,
        warehouse=warehouse,
        batch_number="LATER",
        quantity=5,
        expiry_date=date.today() + timedelta(days=60),
    )

    assert scan_expiring_batches(days=7) == 1
    assert (
        AnalyticsEvent.objects.filter(store=store, event_type="inventory.batch_expiring").count()
        == 1
    )


def test_scan_ignores_depleted_batches(make_store, make_variant, make_warehouse):
    store, _owner = make_store()
    variant = make_variant(store)
    warehouse = make_warehouse(store)
    StockBatch.objects.create(
        store=store,
        variant=variant,
        warehouse=warehouse,
        batch_number="EMPTY",
        quantity=0,
        expiry_date=date.today() + timedelta(days=1),
    )
    assert scan_expiring_batches(days=7) == 0
