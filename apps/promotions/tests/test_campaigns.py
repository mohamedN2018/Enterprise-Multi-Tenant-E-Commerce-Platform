"""Automatic campaign engine tests (P2.5): flash sales, BXGY, order discounts,
free shipping, validity windows, priority/stacking, RBAC and isolation."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import ProductStatus
from apps.catalog.services import CatalogService
from apps.promotions.models import Campaign, CampaignType, DiscountType
from apps.stores.models import StoreRole

from .conftest import add_to_cart, checkout

pytestmark = pytest.mark.django_db

CAMPAIGNS = reverse("v1:promotions:campaign-list")
ACTIVE = reverse("v1:promotions:campaign-active")


# --- Checkout effects -------------------------------------------------------
def test_flash_sale_discount_at_checkout(make_store, buyer_setup, make_campaign):
    store, _owner = make_store()
    client, _buyer, variant = buyer_setup(store, price="50.00")
    make_campaign(
        store,
        campaign_type=CampaignType.FLASH_SALE,
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("20"),
        products=[variant.product],
    )
    add_to_cart(client, variant, 2)  # subtotal 100
    order = checkout(client).json()["data"]
    assert order["discount_total"] == "20.00"
    assert order["total"] == "80.00"


def test_flash_sale_only_targets_matching_products(make_store, buyer_setup, make_campaign):
    store, _owner = make_store()
    client, _buyer, variant = buyer_setup(store, price="50.00")
    other = CatalogService().create_product(
        store=store, data={"name": "Other", "status": ProductStatus.PUBLISHED}
    )
    make_campaign(
        store,
        campaign_type=CampaignType.FLASH_SALE,
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("50"),
        products=[other],  # not in the cart
    )
    add_to_cart(client, variant, 2)
    order = checkout(client).json()["data"]
    assert order["discount_total"] == "0.00"
    assert order["total"] == "100.00"


def test_order_discount_threshold(make_store, buyer_setup, make_campaign):
    store, _owner = make_store()
    make_campaign(
        store,
        campaign_type=CampaignType.ORDER_DISCOUNT,
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("10"),
        min_spend=Decimal("100"),
    )
    # Below the threshold: no discount.
    c1, _b1, v1 = buyer_setup(store, price="50.00")
    add_to_cart(c1, v1, 1)  # 50 < 100
    assert checkout(c1).json()["data"]["discount_total"] == "0.00"
    # At the threshold: 10% off.
    c2, _b2, v2 = buyer_setup(store, price="50.00")
    add_to_cart(c2, v2, 2)  # 100
    order = checkout(c2).json()["data"]
    assert order["discount_total"] == "10.00"
    assert order["total"] == "90.00"


def test_buy_x_get_y_discounts_cheapest_unit(make_store, buyer_setup, make_campaign):
    store, _owner = make_store()
    client, _buyer, variant = buyer_setup(store, price="30.00")
    make_campaign(
        store,
        campaign_type=CampaignType.BUY_X_GET_Y,
        buy_quantity=2,
        get_quantity=1,
        get_discount_percent=Decimal("100"),  # the 3rd unit is free
        products=[variant.product],
    )
    add_to_cart(client, variant, 3)  # subtotal 90, one free unit
    order = checkout(client).json()["data"]
    assert order["discount_total"] == "30.00"
    assert order["total"] == "60.00"


def test_buy_x_get_y_needs_a_full_group(make_store, buyer_setup, make_campaign):
    store, _owner = make_store()
    client, _buyer, variant = buyer_setup(store, price="30.00")
    make_campaign(
        store,
        campaign_type=CampaignType.BUY_X_GET_Y,
        buy_quantity=2,
        get_quantity=1,
        get_discount_percent=Decimal("100"),
        products=[variant.product],
    )
    add_to_cart(client, variant, 2)  # only 2 units -> no full group
    assert checkout(client).json()["data"]["discount_total"] == "0.00"


def test_free_shipping_campaign_zeroes_shipping(
    make_store, buyer_setup, make_campaign, shipping_method
):
    store, _owner = make_store()
    method = shipping_method(store, price="10.00", countries=("DE",))
    make_campaign(store, campaign_type=CampaignType.FREE_SHIPPING, min_spend=Decimal("50"))
    # Subtotal 100 >= 50 -> shipping waived.
    c1, _b1, v1 = buyer_setup(store, price="50.00")
    add_to_cart(c1, v1, 2)
    order = checkout(c1, method=method, country="DE").json()["data"]
    assert order["shipping_total"] == "0.00"
    assert order["total"] == "100.00"
    # Subtotal 20 < 50 -> shipping still charged.
    c2, _b2, v2 = buyer_setup(store, price="20.00")
    add_to_cart(c2, v2, 1)
    below = checkout(c2, method=method, country="DE").json()["data"]
    assert below["shipping_total"] == "10.00"
    assert below["total"] == "30.00"


# --- Validity window --------------------------------------------------------
def test_inactive_campaign_ignored(make_store, buyer_setup, make_campaign):
    store, _owner = make_store()
    client, _buyer, variant = buyer_setup(store, price="50.00")
    make_campaign(
        store,
        campaign_type=CampaignType.FLASH_SALE,
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("50"),
        products=[variant.product],
        is_active=False,
    )
    add_to_cart(client, variant, 1)
    assert checkout(client).json()["data"]["discount_total"] == "0.00"


def test_out_of_window_campaigns_ignored(make_store, buyer_setup, make_campaign):
    store, _owner = make_store()
    client, _buyer, variant = buyer_setup(store, price="50.00")
    make_campaign(
        store,
        name="expired",
        campaign_type=CampaignType.ORDER_DISCOUNT,
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("10"),
        min_spend=Decimal("0"),
        ends_at=timezone.now() - timedelta(days=1),
    )
    make_campaign(
        store,
        name="future",
        campaign_type=CampaignType.ORDER_DISCOUNT,
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("10"),
        min_spend=Decimal("0"),
        starts_at=timezone.now() + timedelta(days=1),
    )
    add_to_cart(client, variant, 1)
    assert checkout(client).json()["data"]["discount_total"] == "0.00"


# --- Priority & stacking ----------------------------------------------------
def test_stackable_campaigns_combine(make_store, buyer_setup, make_campaign):
    store, _owner = make_store()
    client, _buyer, variant = buyer_setup(store, price="50.00")
    for name, prio in (("a", 1), ("b", 2)):
        make_campaign(
            store,
            name=name,
            campaign_type=CampaignType.ORDER_DISCOUNT,
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("10"),
            min_spend=Decimal("0"),
            priority=prio,
        )
    add_to_cart(client, variant, 2)  # subtotal 100
    order = checkout(client).json()["data"]
    assert order["discount_total"] == "20.00"  # 10% + 10%
    assert order["total"] == "80.00"


def test_non_stackable_campaign_is_exclusive(make_store, buyer_setup, make_campaign):
    store, _owner = make_store()
    client, _buyer, variant = buyer_setup(store, price="50.00")
    make_campaign(
        store,
        name="stackable-10pct",
        campaign_type=CampaignType.ORDER_DISCOUNT,
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("10"),
        min_spend=Decimal("0"),
        priority=1,
        stackable=True,
    )
    make_campaign(
        store,
        name="exclusive-30off",
        campaign_type=CampaignType.ORDER_DISCOUNT,
        discount_type=DiscountType.FIXED,
        discount_value=Decimal("30"),
        min_spend=Decimal("0"),
        priority=5,  # higher priority wins and locks out the other
        stackable=False,
    )
    add_to_cart(client, variant, 2)  # subtotal 100
    order = checkout(client).json()["data"]
    assert order["discount_total"] == "30.00"  # only the exclusive campaign
    assert order["total"] == "70.00"


def test_no_campaigns_checkout_unchanged(make_store, buyer_setup):
    store, _owner = make_store()
    client, _buyer, variant = buyer_setup(store, price="50.00")
    add_to_cart(client, variant, 2)
    order = checkout(client).json()["data"]
    assert order["discount_total"] == "0.00"
    assert order["total"] == "100.00"


# --- Management API ---------------------------------------------------------
def test_campaign_crud_rbac(make_store, make_user, add_member, store_client):
    store, owner = make_store()
    payload = {
        "name": "Autumn sale",
        "campaign_type": "order_discount",
        "discount_type": "percentage",
        "discount_value": "10",
    }
    employee = make_user()
    add_member(store, employee, StoreRole.EMPLOYEE)
    denied = store_client(employee, store).post(CAMPAIGNS, payload, format="json")
    assert denied.status_code == 403
    created = store_client(owner, store).post(CAMPAIGNS, payload, format="json")
    assert created.status_code == 201


def test_campaign_type_requires_its_config(make_store, store_client):
    store, owner = make_store()
    # buy_x_get_y without quantities is rejected by the serializer.
    resp = store_client(owner, store).post(
        CAMPAIGNS, {"name": "BXGY", "campaign_type": "buy_x_get_y"}, format="json"
    )
    assert resp.status_code == 400


def test_attach_product_and_reject_duplicate(make_store, buyer_setup, make_campaign, store_client):
    store, owner = make_store()
    _client, _buyer, variant = buyer_setup(store)
    campaign = make_campaign(
        store,
        campaign_type=CampaignType.FLASH_SALE,
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("10"),
    )
    url = reverse("v1:promotions:campaign-product-list", kwargs={"campaign_id": str(campaign.id)})
    oc = store_client(owner, store)
    assert oc.post(url, {"product": str(variant.product_id)}, format="json").status_code == 201
    dup = oc.post(url, {"product": str(variant.product_id)}, format="json")
    assert dup.status_code == 409
    assert len(oc.get(url).json()["data"]) == 1


def test_active_campaigns_endpoint_lists_live_only(
    make_store, make_user, make_campaign, store_client
):
    store, _owner = make_store()
    make_campaign(
        store,
        name="live",
        campaign_type=CampaignType.ORDER_DISCOUNT,
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("10"),
    )
    make_campaign(
        store,
        name="off",
        campaign_type=CampaignType.ORDER_DISCOUNT,
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("10"),
        is_active=False,
    )
    resp = store_client(make_user(), store).get(ACTIVE)
    assert resp.status_code == 200
    assert [c["name"] for c in resp.json()["data"]] == ["live"]


def test_campaigns_are_store_scoped(make_store):
    store_a, _owner_a = make_store(name="A")
    store_b, _owner_b = make_store(name="B")
    Campaign.objects.create(store=store_a, name="A-only", campaign_type=CampaignType.FREE_SHIPPING)
    assert Campaign.objects.filter(store=store_a).count() == 1
    assert Campaign.objects.filter(store=store_b).count() == 0
