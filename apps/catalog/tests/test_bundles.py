"""Bundle / kit / composite product tests (P2.1a).

Covers component management, bundle availability = min(required components),
checkout reserving component stock, and backward-compatibility of simple products.
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest
from django.urls import reverse

from apps.catalog.models import ProductKind, ProductStatus
from apps.catalog.services import BundleService, CatalogService
from apps.inventory.models import StockItem, Warehouse
from apps.inventory.services import InventoryService
from apps.orders.models import OrderStatus
from apps.stores.models import StoreRole

pytestmark = pytest.mark.django_db

ADD_ITEM = reverse("v1:cart:item-add")
CHECKOUT = reverse("v1:cart:checkout")


def _components_url(product_id):
    return reverse("v1:catalog:component-list", kwargs={"product_id": product_id})


def _published_variant(store, *, sku, price="10.00", stock=0):
    cat = CatalogService()
    product = cat.create_product(
        store=store, data={"name": f"P-{sku}", "status": ProductStatus.PUBLISHED}
    )
    variant = cat.create_variant(
        store=store, product=product, data={"sku": sku, "price": Decimal(price)}
    )
    if stock:
        warehouse, _ = Warehouse.objects.get_or_create(
            store=store, code="MAIN", defaults={"name": "Main"}
        )
        InventoryService().receive(
            store=store, variant=variant, warehouse=warehouse, quantity=stock
        )
    return variant


def _build_bundle(store, *, stock_a=10, stock_b=6):
    va = _published_variant(store, sku="A", price="10", stock=stock_a)
    vb = _published_variant(store, sku="B", price="20", stock=stock_b)
    bundle = CatalogService().create_product(
        store=store,
        data={"name": "Combo", "kind": ProductKind.BUNDLE, "status": ProductStatus.PUBLISHED},
    )
    bundle_variant = CatalogService().create_variant(
        store=store, product=bundle, data={"sku": "COMBO", "price": Decimal("25.00")}
    )
    service = BundleService()
    service.add_component(store=store, bundle=bundle, component_variant_id=va.id, quantity=1)
    service.add_component(store=store, bundle=bundle, component_variant_id=vb.id, quantity=2)
    return SimpleNamespace(bundle=bundle, bundle_variant=bundle_variant, va=va, vb=vb)


def test_create_product_with_kind(store_client, make_store):
    store, owner = make_store()
    resp = store_client(owner, store).post(
        reverse("v1:catalog:product-list"),
        {"name": "My Bundle", "kind": "bundle"},
        format="json",
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["kind"] == "bundle"


def test_add_and_list_components(store_client, make_store):
    store, owner = make_store()
    bundle = CatalogService().create_product(
        store=store, data={"name": "B", "kind": ProductKind.BUNDLE}
    )
    component = _published_variant(store, sku="C1", stock=5)
    client = store_client(owner, store)
    resp = client.post(
        _components_url(bundle.id),
        {"component_variant_id": str(component.id), "quantity": 2},
        format="json",
    )
    assert resp.status_code == 201
    listing = client.get(_components_url(bundle.id)).json()["data"]
    assert len(listing) == 1
    assert listing[0]["quantity"] == 2


def test_availability_is_min_of_required_components(store_client, make_store, make_user):
    store, _owner = make_store()
    data = _build_bundle(store, stock_a=10, stock_b=6)  # min(10//1, 6//2) = 3
    buyer = make_user()
    client = store_client(buyer, store)
    # qty 3 fits.
    ok = client.post(
        ADD_ITEM, {"variant_id": str(data.bundle_variant.id), "quantity": 3}, format="json"
    )
    assert ok.status_code == 201
    # qty 4 exceeds availability.
    over = store_client(make_user(), store).post(
        ADD_ITEM, {"variant_id": str(data.bundle_variant.id), "quantity": 4}, format="json"
    )
    assert over.status_code == 422
    assert over.json()["error_code"] == "insufficient_stock"


def test_checkout_reserves_components_and_confirm_deducts(store_client, make_store, make_user):
    store, _owner = make_store()
    data = _build_bundle(store, stock_a=10, stock_b=6)
    client = store_client(make_user(), store)
    client.post(ADD_ITEM, {"variant_id": str(data.bundle_variant.id), "quantity": 2}, format="json")

    order = client.post(CHECKOUT).json()["data"]
    assert order["status"] == OrderStatus.PENDING
    # Components reserved: A 2*1=2, B 2*2=4.
    assert StockItem.objects.get(variant=data.va).reserved_quantity == 2
    assert StockItem.objects.get(variant=data.vb).reserved_quantity == 4

    confirm = reverse("v1:orders:confirm", kwargs={"order_id": order["id"]})
    client.post(confirm)
    assert StockItem.objects.get(variant=data.va).quantity == 8
    assert StockItem.objects.get(variant=data.vb).quantity == 2


def test_bundle_without_components_is_unavailable(store_client, make_store, make_user):
    store, _owner = make_store()
    bundle = CatalogService().create_product(
        store=store,
        data={"name": "Empty", "kind": ProductKind.BUNDLE, "status": ProductStatus.PUBLISHED},
    )
    variant = CatalogService().create_variant(
        store=store, product=bundle, data={"sku": "EMPTY", "price": Decimal("9.99")}
    )
    resp = store_client(make_user(), store).post(
        ADD_ITEM, {"variant_id": str(variant.id), "quantity": 1}, format="json"
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "insufficient_stock"


def test_component_from_other_store_rejected(store_client, make_store):
    store_a, owner_a = make_store(name="A")
    store_b, _owner_b = make_store(name="B")
    bundle_a = CatalogService().create_product(
        store=store_a, data={"name": "BA", "kind": ProductKind.BUNDLE}
    )
    variant_b = _published_variant(store_b, sku="BVAR", stock=5)
    resp = store_client(owner_a, store_a).post(
        _components_url(bundle_a.id),
        {"component_variant_id": str(variant_b.id)},
        format="json",
    )
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "variant_not_found"


def test_nested_bundle_rejected(store_client, make_store):
    store, owner = make_store()
    data = _build_bundle(store)
    outer = CatalogService().create_product(
        store=store, data={"name": "Outer", "kind": ProductKind.BUNDLE}
    )
    resp = store_client(owner, store).post(
        _components_url(outer.id),
        {"component_variant_id": str(data.bundle_variant.id)},
        format="json",
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "nested_bundle_unsupported"


def test_employee_cannot_add_component(store_client, make_store, make_user, add_member):
    store, _owner = make_store()
    bundle = CatalogService().create_product(
        store=store, data={"name": "B", "kind": ProductKind.BUNDLE}
    )
    component = _published_variant(store, sku="C", stock=5)
    employee = make_user()
    add_member(store, employee, StoreRole.EMPLOYEE)
    resp = store_client(employee, store).post(
        _components_url(bundle.id),
        {"component_variant_id": str(component.id)},
        format="json",
    )
    assert resp.status_code == 403


def test_adding_components_to_simple_product_rejected(store_client, make_store):
    store, owner = make_store()
    simple = CatalogService().create_product(store=store, data={"name": "Simple"})
    component = _published_variant(store, sku="C", stock=5)
    resp = store_client(owner, store).post(
        _components_url(simple.id),
        {"component_variant_id": str(component.id)},
        format="json",
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "not_a_bundle"
