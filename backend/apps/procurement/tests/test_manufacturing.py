"""Manufacturing / BOM tests (deferred follow-up): bills of materials + work orders."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.core.exceptions import BusinessRuleError, ConflictError
from apps.inventory.models import StockItem
from apps.inventory.services import InventoryService
from apps.procurement.models import BillOfMaterials
from apps.procurement.services import ManufacturingService
from apps.stores.models import StoreRole

pytestmark = pytest.mark.django_db


def _qty(store, variant, warehouse) -> int:
    item = StockItem.objects.filter(store=store, variant=variant, warehouse=warehouse).first()
    return item.quantity if item else 0


def test_complete_work_order_consumes_components_and_produces_output(
    make_store, make_variant, make_warehouse
):
    store, _owner = make_store()
    warehouse = make_warehouse(store)
    output, comp_a, comp_b = make_variant(store), make_variant(store), make_variant(store)
    inventory = InventoryService()
    inventory.receive(store=store, variant=comp_a, warehouse=warehouse, quantity=20)
    inventory.receive(store=store, variant=comp_b, warehouse=warehouse, quantity=20)

    service = ManufacturingService()
    bom = service.create_bom(store=store, output_variant=output, name="Widget")
    service.add_component(store=store, bom=bom, component_variant=comp_a, quantity=2)
    service.add_component(store=store, bom=bom, component_variant=comp_b, quantity=1)
    work_order = service.create_work_order(store=store, bom=bom, warehouse=warehouse, quantity=5)
    service.complete_work_order(work_order=work_order)

    assert _qty(store, comp_a, warehouse) == 10  # 20 - 2*5
    assert _qty(store, comp_b, warehouse) == 15  # 20 - 1*5
    assert _qty(store, output, warehouse) == 5  # produced
    work_order.refresh_from_db()
    assert work_order.status == "completed"


def test_complete_rolls_back_when_components_short(make_store, make_variant, make_warehouse):
    store, _owner = make_store()
    warehouse = make_warehouse(store)
    output, comp = make_variant(store), make_variant(store)
    InventoryService().receive(store=store, variant=comp, warehouse=warehouse, quantity=3)

    service = ManufacturingService()
    bom = service.create_bom(store=store, output_variant=output, name="Widget")
    service.add_component(store=store, bom=bom, component_variant=comp, quantity=2)
    work_order = service.create_work_order(store=store, bom=bom, warehouse=warehouse, quantity=5)

    with pytest.raises(BusinessRuleError):
        service.complete_work_order(work_order=work_order)  # needs 10, only 3 on hand
    work_order.refresh_from_db()
    assert work_order.status == "draft"  # rolled back
    assert _qty(store, comp, warehouse) == 3  # component untouched
    assert _qty(store, output, warehouse) == 0  # nothing produced


def test_create_bom_rejects_duplicate(make_store, make_variant):
    store, _owner = make_store()
    output = make_variant(store)
    service = ManufacturingService()
    service.create_bom(store=store, output_variant=output, name="A")
    with pytest.raises(ConflictError):
        service.create_bom(store=store, output_variant=output, name="B")


def test_self_component_is_rejected(make_store, make_variant):
    store, _owner = make_store()
    output = make_variant(store)
    service = ManufacturingService()
    bom = service.create_bom(store=store, output_variant=output, name="A")
    with pytest.raises(BusinessRuleError):
        service.add_component(store=store, bom=bom, component_variant=output, quantity=1)


def test_completed_work_order_cannot_be_cancelled(make_store, make_variant, make_warehouse):
    store, _owner = make_store()
    warehouse = make_warehouse(store)
    output, comp = make_variant(store), make_variant(store)
    InventoryService().receive(store=store, variant=comp, warehouse=warehouse, quantity=10)
    service = ManufacturingService()
    bom = service.create_bom(store=store, output_variant=output, name="A")
    service.add_component(store=store, bom=bom, component_variant=comp, quantity=1)
    work_order = service.create_work_order(store=store, bom=bom, warehouse=warehouse, quantity=2)
    service.complete_work_order(work_order=work_order)
    with pytest.raises(ConflictError):
        service.cancel_work_order(work_order=work_order)


def test_create_bom_via_api_rbac(make_store, make_variant, make_user, add_member, store_client):
    store, owner = make_store()
    output = make_variant(store)
    url = reverse("v1:procurement:bom-list")
    payload = {"output_variant_id": str(output.id), "name": "Widget"}
    employee = make_user()
    add_member(store, employee, StoreRole.EMPLOYEE)
    assert store_client(employee, store).post(url, payload, format="json").status_code == 403
    assert store_client(owner, store).post(url, payload, format="json").status_code == 201


def test_boms_are_store_scoped(make_store, make_variant):
    store_a, _owner_a = make_store(name="A")
    store_b, _owner_b = make_store(name="B")
    ManufacturingService().create_bom(
        store=store_a, output_variant=make_variant(store_a), name="A-only"
    )
    assert BillOfMaterials.objects.filter(store=store_a).count() == 1
    assert BillOfMaterials.objects.filter(store=store_b).count() == 0
