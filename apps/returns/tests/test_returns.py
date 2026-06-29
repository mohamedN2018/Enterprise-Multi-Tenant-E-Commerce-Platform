"""Returns / RMA tests (P2.7)."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.inventory.models import StockItem
from apps.returns.models import ReturnStatus
from apps.stores.models import StoreRole

pytestmark = pytest.mark.django_db

RETURNS = reverse("v1:returns:list")
WALLET = reverse("v1:rewards:wallet")


def _order_item_id(order):
    return order["items"][0]["id"]


def _create_return(client, order, qty=1):
    return client.post(
        RETURNS,
        {
            "order_id": order["id"],
            "items": [{"order_item_id": _order_item_id(order), "quantity": qty}],
        },
        format="json",
    )


def test_create_return(make_store, make_user, make_variant, confirmed_order):
    store, _owner = make_store()
    variant = make_variant(store, price="50.00")
    client, order = confirmed_order(store, make_user(), variant, qty=2)
    resp = _create_return(client, order, qty=1)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["status"] == ReturnStatus.REQUESTED
    assert data["refund_amount"] == "50.00"


def test_cannot_return_unconfirmed_order(make_store, make_user, make_variant, store_client):
    store, _owner = make_store()
    variant = make_variant(store, price="50.00")
    buyer = make_user()
    client = store_client(buyer, store)
    client.post(
        reverse("v1:cart:item-add"), {"variant_id": str(variant.id), "quantity": 1}, format="json"
    )
    order = client.post(reverse("v1:cart:checkout")).json()["data"]  # PENDING (not confirmed)
    resp = _create_return(client, order, qty=1)
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "order_not_returnable"


def test_return_quantity_guard(make_store, make_user, make_variant, confirmed_order):
    store, _owner = make_store()
    variant = make_variant(store, price="50.00")
    client, order = confirmed_order(store, make_user(), variant, qty=2)
    resp = _create_return(client, order, qty=5)  # only 2 ordered
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "invalid_return_quantity"


def test_approve_and_refund_credits_wallet_and_restocks(
    make_store, make_user, make_variant, confirmed_order, store_client
):
    store, owner = make_store()
    variant = make_variant(store, price="50.00", stock=10)
    buyer = make_user()
    client, order = confirmed_order(store, buyer, variant, qty=2)  # stock 10 -> 8
    rma = _create_return(client, order, qty=1).json()["data"]

    staff = store_client(owner, store)
    staff.post(reverse("v1:returns:approve", kwargs={"return_id": rma["id"]}))
    refunded = staff.post(reverse("v1:returns:refund", kwargs={"return_id": rma["id"]}))
    assert refunded.status_code == 200
    assert refunded.json()["data"]["status"] == ReturnStatus.REFUNDED

    # Restocked: 8 + 1 = 9.
    assert StockItem.objects.get(variant=variant).quantity == 9
    # Buyer credited 50.00 to wallet.
    assert client.get(WALLET).json()["data"]["balance"] == "50.00"


def test_refund_requires_approval(
    make_store, make_user, make_variant, confirmed_order, store_client
):
    store, owner = make_store()
    variant = make_variant(store, price="50.00")
    client, order = confirmed_order(store, make_user(), variant, qty=2)
    rma = _create_return(client, order, qty=1).json()["data"]
    resp = store_client(owner, store).post(
        reverse("v1:returns:refund", kwargs={"return_id": rma["id"]})
    )
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "not_refundable"


def test_reject_frees_quantity(make_store, make_user, make_variant, confirmed_order, store_client):
    store, owner = make_store()
    variant = make_variant(store, price="50.00")
    buyer = make_user()
    client, order = confirmed_order(store, buyer, variant, qty=2)
    rma = _create_return(client, order, qty=2).json()["data"]

    store_client(owner, store).post(reverse("v1:returns:reject", kwargs={"return_id": rma["id"]}))
    # After rejection the full quantity can be requested again.
    again = _create_return(client, order, qty=2)
    assert again.status_code == 201


def test_buyer_can_cancel(make_store, make_user, make_variant, confirmed_order):
    store, _owner = make_store()
    variant = make_variant(store, price="50.00")
    client, order = confirmed_order(store, make_user(), variant, qty=1)
    rma = _create_return(client, order, qty=1).json()["data"]
    resp = client.post(reverse("v1:returns:cancel", kwargs={"return_id": rma["id"]}))
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == ReturnStatus.CANCELLED


def test_employee_cannot_approve(
    make_store, make_user, make_variant, confirmed_order, store_client, add_member
):
    store, _owner = make_store()
    variant = make_variant(store, price="50.00")
    client, order = confirmed_order(store, make_user(), variant, qty=1)
    rma = _create_return(client, order, qty=1).json()["data"]
    employee = make_user()
    add_member(store, employee, StoreRole.EMPLOYEE)
    resp = store_client(employee, store).post(
        reverse("v1:returns:approve", kwargs={"return_id": rma["id"]})
    )
    assert resp.status_code == 403


def test_returns_scoped_to_buyer(
    make_store, make_user, make_variant, confirmed_order, store_client
):
    store, _owner = make_store()
    variant = make_variant(store, price="50.00")
    client, order = confirmed_order(store, make_user(), variant, qty=1)
    _create_return(client, order, qty=1)
    other = store_client(make_user(), store)
    assert other.get(RETURNS).json()["meta"]["pagination"]["count"] == 0
