"""Pricing engine tests (P2.3)."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.pricing.models import CustomerGroup, PriceRule
from apps.stores.models import StoreRole

pytestmark = pytest.mark.django_db

GROUPS = reverse("v1:pricing:group-list")
RULES = reverse("v1:pricing:rule-list")
QUOTE = reverse("v1:pricing:quote")
CART_ADD = reverse("v1:cart:item-add")
CART = reverse("v1:cart:cart")


def _quote(client, variant, quantity=1):
    return client.get(QUOTE, {"variant": str(variant.id), "quantity": quantity})


def _create_rule(client, variant, *, value, rule_type="fixed", min_quantity=1, group_id=None):
    payload = {
        "variant_id": str(variant.id),
        "value": str(value),
        "rule_type": rule_type,
        "min_quantity": min_quantity,
    }
    if group_id:
        payload["customer_group_id"] = str(group_id)
    return client.post(RULES, payload, format="json")


# --- Customer groups -------------------------------------------------------
def test_create_group_autocode(store_client, make_store):
    store, owner = make_store()
    resp = store_client(owner, store).post(GROUPS, {"name": "Wholesale"}, format="json")
    assert resp.status_code == 201
    assert resp.json()["data"]["code"] == "wholesale"


def test_assign_member(store_client, make_store, make_user):
    store, owner = make_store()
    group = CustomerGroup.objects.create(store=store, name="VIP", code="vip")
    buyer = make_user()
    resp = store_client(owner, store).post(
        reverse("v1:pricing:group-members", kwargs={"group_id": group.id}),
        {"email": buyer.email},
        format="json",
    )
    assert resp.status_code == 201
    assert group.memberships.filter(user=buyer).exists()


def test_employee_cannot_create_group(store_client, make_store, make_user, add_member):
    store, _owner = make_store()
    employee = make_user()
    add_member(store, employee, StoreRole.EMPLOYEE)
    resp = store_client(employee, store).post(GROUPS, {"name": "X"}, format="json")
    assert resp.status_code == 403


# --- Price resolution ------------------------------------------------------
def test_fixed_rule(store_client, make_store, make_user, make_variant):
    store, owner = make_store()
    variant = make_variant(store, price="100.00")
    _create_rule(store_client(owner, store), variant, value="80.00")
    quote = _quote(store_client(make_user(), store), variant)
    assert quote.json()["data"]["unit_price"] == "80.00"


def test_percent_rule(store_client, make_store, make_user, make_variant):
    store, owner = make_store()
    variant = make_variant(store, price="100.00")
    _create_rule(store_client(owner, store), variant, value="20", rule_type="percent_discount")
    quote = _quote(store_client(make_user(), store), variant)
    assert quote.json()["data"]["unit_price"] == "80.00"


def test_percent_over_100_rejected(store_client, make_store, make_variant):
    """A >100% discount would resolve to a negative unit price — reject at input."""
    store, owner = make_store()
    variant = make_variant(store, price="100.00")
    resp = _create_rule(
        store_client(owner, store), variant, value="150", rule_type="percent_discount"
    )
    assert resp.status_code == 400


def test_resolved_price_never_negative(store_client, make_store, make_user, make_variant):
    """Defense in depth: even a malformed stored rule cannot credit the buyer."""
    store, _owner = make_store()
    variant = make_variant(store, price="100.00")
    # Bypass the serializer to persist an out-of-range rule directly.
    PriceRule.objects.create(
        store=store, variant=variant, rule_type="percent_discount", value="500"
    )
    quote = _quote(store_client(make_user(), store), variant)
    assert quote.json()["data"]["unit_price"] == "0.00"


def test_tier_pricing(store_client, make_store, make_user, make_variant):
    store, owner = make_store()
    variant = make_variant(store, price="100.00")
    _create_rule(store_client(owner, store), variant, value="70.00", min_quantity=10)
    client = store_client(make_user(), store)
    assert _quote(client, variant, quantity=5).json()["data"]["unit_price"] == "100.00"
    assert _quote(client, variant, quantity=10).json()["data"]["unit_price"] == "70.00"


def test_best_of_multiple_rules(store_client, make_store, make_user, make_variant):
    store, owner = make_store()
    variant = make_variant(store, price="100.00")
    owner_client = store_client(owner, store)
    _create_rule(owner_client, variant, value="10", rule_type="percent_discount")  # -> 90
    _create_rule(owner_client, variant, value="85.00")  # fixed 85
    quote = _quote(store_client(make_user(), store), variant)
    assert quote.json()["data"]["unit_price"] == "85.00"


def test_group_specific_rule(store_client, make_store, make_user, make_variant):
    store, owner = make_store()
    variant = make_variant(store, price="100.00")
    owner_client = store_client(owner, store)
    group = CustomerGroup.objects.create(store=store, name="Wholesale", code="wholesale")
    _create_rule(owner_client, variant, value="60.00", group_id=group.id)

    buyer = make_user()
    # Not in the group -> base price.
    assert _quote(store_client(buyer, store), variant).json()["data"]["unit_price"] == "100.00"
    # Assign to the group -> group price.
    owner_client.post(
        reverse("v1:pricing:group-members", kwargs={"group_id": group.id}),
        {"email": buyer.email},
        format="json",
    )
    assert _quote(store_client(buyer, store), variant).json()["data"]["unit_price"] == "60.00"


# --- Cart integration ------------------------------------------------------
def test_cart_applies_resolved_price(store_client, make_store, make_user, make_variant):
    store, owner = make_store()
    variant = make_variant(store, price="100.00")
    _create_rule(store_client(owner, store), variant, value="80.00")

    client = store_client(make_user(), store)
    client.post(CART_ADD, {"variant_id": str(variant.id), "quantity": 2}, format="json")
    cart = client.get(CART).json()["data"]
    assert cart["subtotal"] == "160.00"  # 2 x 80


def test_no_rules_uses_base_price(store_client, make_store, make_user, make_variant):
    store, _owner = make_store()
    variant = make_variant(store, price="100.00")
    client = store_client(make_user(), store)
    client.post(CART_ADD, {"variant_id": str(variant.id), "quantity": 1}, format="json")
    assert client.get(CART).json()["data"]["subtotal"] == "100.00"


def test_rules_are_store_scoped(store_client, make_store, make_variant):
    store_a, owner_a = make_store(name="A")
    store_b, owner_b = make_store(name="B")
    variant_a = make_variant(store_a, price="100.00")
    _create_rule(store_client(owner_a, store_a), variant_a, value="50.00")
    # Store B owner querying rules sees none of A's.
    resp = store_client(owner_b, store_b).get(RULES)
    assert resp.json()["meta"]["pagination"]["count"] == 0
    assert PriceRule.objects.filter(store=store_a).count() == 1
