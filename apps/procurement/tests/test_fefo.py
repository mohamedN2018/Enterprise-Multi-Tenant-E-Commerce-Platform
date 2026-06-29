"""Batch-FEFO consumption tests (deferred follow-up): deplete lots first-expiry-first."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.catalog.models import ProductStatus
from apps.catalog.services import CatalogService
from apps.inventory.models import StockItem
from apps.inventory.services import InventoryService
from apps.procurement.models import StockBatch
from apps.procurement.services import ProcurementService

pytestmark = pytest.mark.django_db


def _batch(store, variant, warehouse, *, number, qty, days):
    return StockBatch.objects.create(
        store=store,
        variant=variant,
        warehouse=warehouse,
        batch_number=number,
        quantity=qty,
        expiry_date=date.today() + timedelta(days=days),
    )


def test_consume_batches_fefo_orders_by_expiry(make_store, make_variant, make_warehouse):
    store, _owner = make_store()
    variant = make_variant(store)
    warehouse = make_warehouse(store)
    late = _batch(store, variant, warehouse, number="LATE", qty=5, days=30)
    early = _batch(store, variant, warehouse, number="EARLY", qty=5, days=5)

    consumed = ProcurementService().consume_batches_fefo(
        store=store, variant=variant, warehouse=warehouse, quantity=7
    )
    assert consumed == 7
    early.refresh_from_db()
    late.refresh_from_db()
    assert early.quantity == 0  # earliest expiry fully consumed first
    assert late.quantity == 3  # remainder taken from the later lot


def test_issue_depletes_batches_via_signal(make_store, make_variant, make_warehouse):
    store, _owner = make_store()
    variant = make_variant(store)
    warehouse = make_warehouse(store)
    InventoryService().receive(store=store, variant=variant, warehouse=warehouse, quantity=10)
    _batch(store, variant, warehouse, number="B1", qty=10, days=10)

    InventoryService().issue(
        store=store, variant=variant, warehouse=warehouse, quantity=4, reference="production"
    )
    assert StockBatch.objects.get(store=store, batch_number="B1").quantity == 6
    assert StockItem.objects.get(store=store, variant=variant, warehouse=warehouse).quantity == 6


def test_issue_without_batches_is_a_noop_for_fefo(make_store, make_variant, make_warehouse):
    store, _owner = make_store()
    variant = make_variant(store)
    warehouse = make_warehouse(store)
    InventoryService().receive(store=store, variant=variant, warehouse=warehouse, quantity=10)
    item = InventoryService().issue(store=store, variant=variant, warehouse=warehouse, quantity=3)
    assert item.quantity == 7  # deduction works even with no batches to attribute


def test_sale_commit_depletes_batches(make_store, make_warehouse, make_user, store_client):
    store, _owner = make_store()
    warehouse = make_warehouse(store)
    product = CatalogService().create_product(
        store=store, data={"name": "Perishable", "status": ProductStatus.PUBLISHED}
    )
    variant = CatalogService().create_variant(
        store=store, product=product, data={"sku": "SKU-FEFO", "price": Decimal("10.00")}
    )
    InventoryService().receive(store=store, variant=variant, warehouse=warehouse, quantity=10)
    _batch(store, variant, warehouse, number="LOT", qty=10, days=10)

    client = store_client(make_user(), store)
    client.post(
        reverse("v1:cart:item-add"), {"variant_id": str(variant.id), "quantity": 3}, format="json"
    )
    order = client.post(reverse("v1:cart:checkout")).json()["data"]
    client.post(reverse("v1:orders:confirm", kwargs={"order_id": order["id"]}))

    assert StockBatch.objects.get(store=store, batch_number="LOT").quantity == 7
