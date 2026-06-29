"""Configurable products + attributes tests (P2.1c)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.catalog.models import ProductKind, VariantOption
from apps.catalog.services import (
    AttributeService,
    CatalogService,
    ConfigurableProductService,
)
from apps.stores.models import StoreRole

pytestmark = pytest.mark.django_db

ATTRIBUTES = reverse("v1:catalog:attribute-list")
PRODUCT_LIST = reverse("v1:catalog:product-list")


def _values_url(attribute_id):
    return reverse("v1:catalog:attribute-values", kwargs={"attribute_id": attribute_id})


def _product_attrs_url(product_id):
    return reverse("v1:catalog:product-attribute-list", kwargs={"product_id": product_id})


def _options_url(product_id, variant_id):
    return reverse(
        "v1:catalog:variant-options",
        kwargs={"product_id": product_id, "variant_id": variant_id},
    )


def _attribute(store, *, name="Color", values=("Red", "Blue")):
    attr = AttributeService().create_attribute(store=store, data={"name": name})
    value_objs = [
        AttributeService().add_value(store=store, attribute=attr, data={"value": v}) for v in values
    ]
    return attr, value_objs


def _configurable(store, *, name="Tee"):
    product = CatalogService().create_product(
        store=store, data={"name": name, "kind": ProductKind.CONFIGURABLE}
    )
    variant = CatalogService().create_variant(
        store=store, product=product, data={"sku": f"{name}-V", "price": Decimal("19.99")}
    )
    return product, variant


def test_create_attribute_autogenerates_code(store_client, make_store):
    store, owner = make_store()
    resp = store_client(owner, store).post(ATTRIBUTES, {"name": "Shoe Size"}, format="json")
    assert resp.status_code == 201
    assert resp.json()["data"]["code"] == "shoe-size"


def test_add_values_and_duplicate(store_client, make_store):
    store, owner = make_store()
    attr, _ = _attribute(store, values=())
    client = store_client(owner, store)
    assert client.post(_values_url(attr.id), {"value": "Red"}, format="json").status_code == 201
    dupe = client.post(_values_url(attr.id), {"value": "Red"}, format="json")
    assert dupe.status_code == 409
    assert dupe.json()["error_code"] == "value_exists"


def test_declare_attribute_on_configurable(store_client, make_store):
    store, owner = make_store()
    attr, _ = _attribute(store)
    product, _variant = _configurable(store)
    resp = store_client(owner, store).post(
        _product_attrs_url(product.id), {"attribute_id": str(attr.id)}, format="json"
    )
    assert resp.status_code == 201


def test_cannot_declare_attribute_on_simple_product(store_client, make_store):
    store, owner = make_store()
    attr, _ = _attribute(store)
    simple = CatalogService().create_product(store=store, data={"name": "Simple"})
    resp = store_client(owner, store).post(
        _product_attrs_url(simple.id), {"attribute_id": str(attr.id)}, format="json"
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "not_configurable"


def test_set_variant_options(store_client, make_store):
    store, owner = make_store()
    attr, values = _attribute(store)
    product, variant = _configurable(store)
    ConfigurableProductService().add_product_attribute(
        store=store, product=product, attribute_id=attr.id
    )
    resp = store_client(owner, store).put(
        _options_url(product.id, variant.id),
        {"attribute_value_ids": [str(values[0].id)]},
        format="json",
    )
    assert resp.status_code == 200
    assert VariantOption.objects.filter(variant=variant).count() == 1
    listing = store_client(owner, store).get(_options_url(product.id, variant.id)).json()["data"]
    assert listing[0]["attribute"] == "Color"
    assert listing[0]["value"] == "Red"


def test_option_value_must_be_declared(store_client, make_store):
    store, owner = make_store()
    attr, values = _attribute(store)
    product, variant = _configurable(store)
    # Attribute NOT declared on the product.
    resp = store_client(owner, store).put(
        _options_url(product.id, variant.id),
        {"attribute_value_ids": [str(values[0].id)]},
        format="json",
    )
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "attribute_not_declared"


def test_two_values_same_attribute_rejected(store_client, make_store):
    store, owner = make_store()
    attr, values = _attribute(store)  # Red, Blue (both Color)
    product, variant = _configurable(store)
    ConfigurableProductService().add_product_attribute(
        store=store, product=product, attribute_id=attr.id
    )
    resp = store_client(owner, store).put(
        _options_url(product.id, variant.id),
        {"attribute_value_ids": [str(values[0].id), str(values[1].id)]},
        format="json",
    )
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "duplicate_attribute"


def test_filter_products_by_attribute_value(store_client, make_store):
    store, owner = make_store()
    attr, values = _attribute(store)  # Red, Blue
    red, blue = values

    p1, v1 = _configurable(store, name="Red Tee")
    p2, v2 = _configurable(store, name="Blue Tee")
    service = ConfigurableProductService()
    for product in (p1, p2):
        service.add_product_attribute(store=store, product=product, attribute_id=attr.id)
    service.set_variant_options(store=store, variant=v1, attribute_value_ids=[red.id])
    service.set_variant_options(store=store, variant=v2, attribute_value_ids=[blue.id])

    resp = store_client(owner, store).get(PRODUCT_LIST, {"attribute_value": str(red.id)})
    assert resp.status_code == 200
    ids = {row["id"] for row in resp.json()["data"]}
    assert str(p1.id) in ids
    assert str(p2.id) not in ids


def test_employee_cannot_create_attribute(store_client, make_store, make_user, add_member):
    store, _owner = make_store()
    employee = make_user()
    add_member(store, employee, StoreRole.EMPLOYEE)
    resp = store_client(employee, store).post(ATTRIBUTES, {"name": "Size"}, format="json")
    assert resp.status_code == 403


def test_attributes_are_store_scoped(store_client, make_store):
    store_a, owner_a = make_store(name="A")
    store_b, owner_b = make_store(name="B")
    _attribute(store_a, name="Material")
    assert store_client(owner_b, store_b).get(ATTRIBUTES).json()["meta"]["pagination"]["count"] == 0
    assert store_client(owner_a, store_a).get(ATTRIBUTES).json()["meta"]["pagination"]["count"] == 1
