"""Variant-matrix auto-generation tests (P2.1 follow-up)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.catalog.models import ProductKind
from apps.catalog.services import AttributeService, CatalogService, ConfigurableProductService
from apps.core.exceptions import BusinessRuleError

pytestmark = pytest.mark.django_db


def _attr(store, name, values):
    attr = AttributeService().create_attribute(store=store, data={"name": name})
    value_objs = [
        AttributeService().add_value(store=store, attribute=attr, data={"value": v}) for v in values
    ]
    return attr, value_objs


def _configurable_with_axes(store, axes):
    product = CatalogService().create_product(
        store=store, data={"name": "Tee", "kind": ProductKind.CONFIGURABLE}
    )
    declared = []
    for name, values in axes:
        attr, value_objs = _attr(store, name, values)
        ConfigurableProductService().add_product_attribute(
            store=store, product=product, attribute_id=attr.id
        )
        declared.append((attr, value_objs))
    return product, declared


def test_generate_matrix_creates_cartesian_product(make_store):
    store, _owner = make_store()
    product, _ = _configurable_with_axes(
        store, [("Color", ["Red", "Blue"]), ("Size", ["S", "M", "L"])]
    )
    created = ConfigurableProductService().generate_variant_matrix(
        store=store, product=product, base_price=Decimal("20.00")
    )
    assert len(created) == 6  # 2 colours x 3 sizes
    assert all(variant.option_values.count() == 2 for variant in created)
    assert all(variant.price == Decimal("20.00") for variant in created)
    assert product.variants.filter(is_default=True).count() == 1


def test_generate_is_idempotent(make_store):
    store, _owner = make_store()
    product, _ = _configurable_with_axes(store, [("Color", ["Red", "Blue"])])
    service = ConfigurableProductService()
    assert (
        len(service.generate_variant_matrix(store=store, product=product, base_price="10.00")) == 2
    )
    # Re-running adds nothing because every combination already exists.
    assert (
        len(service.generate_variant_matrix(store=store, product=product, base_price="10.00")) == 0
    )
    assert product.variants.count() == 2


def test_generate_after_adding_a_value(make_store):
    store, _owner = make_store()
    product, declared = _configurable_with_axes(store, [("Color", ["Red", "Blue"])])
    service = ConfigurableProductService()
    service.generate_variant_matrix(store=store, product=product, base_price="10.00")
    attr, _values = declared[0]
    AttributeService().add_value(store=store, attribute=attr, data={"value": "Green"})
    new = service.generate_variant_matrix(store=store, product=product, base_price="10.00")
    assert len(new) == 1  # only the new Green combination
    assert product.variants.count() == 3


def test_generate_with_selections_restricts_values(make_store):
    store, _owner = make_store()
    product, declared = _configurable_with_axes(store, [("Color", ["Red", "Blue", "Green"])])
    attr, values = declared[0]
    red = next(v for v in values if v.value == "Red")
    created = ConfigurableProductService().generate_variant_matrix(
        store=store, product=product, base_price="10.00", selections={str(attr.id): [str(red.id)]}
    )
    assert len(created) == 1


def test_generate_requires_configurable_product(make_store):
    store, _owner = make_store()
    simple = CatalogService().create_product(store=store, data={"name": "Simple"})
    with pytest.raises(BusinessRuleError):
        ConfigurableProductService().generate_variant_matrix(
            store=store, product=simple, base_price="10.00"
        )


def test_generate_via_api_applies_prefix(store_client, make_store):
    store, owner = make_store()
    product, _ = _configurable_with_axes(store, [("Color", ["Red", "Blue"])])
    url = reverse("v1:catalog:generate-variants", kwargs={"product_id": str(product.id)})
    resp = store_client(owner, store).post(
        url, {"base_price": "15.00", "sku_prefix": "TEE"}, format="json"
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert len(data) == 2
    assert all(row["sku"].startswith("TEE-") for row in data)
