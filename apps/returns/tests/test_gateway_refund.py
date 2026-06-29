"""Original-gateway refund tests (P2.7 follow-up): refund to the source of payment."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.orders.models import Order, OrderStatus
from apps.payments.models import PaymentStatus
from apps.payments.services import PaymentService
from apps.returns.models import ReturnResolution
from apps.returns.services import ReturnService
from apps.rewards.services import WalletService

pytestmark = pytest.mark.django_db


def _paid_order(store_client, store, buyer, variant, qty=2):
    client = store_client(buyer, store)
    client.post(
        reverse("v1:cart:item-add"),
        {"variant_id": str(variant.id), "quantity": qty},
        format="json",
    )
    order_data = client.post(reverse("v1:cart:checkout")).json()["data"]
    order = Order.objects.get(id=order_data["id"])
    payment = PaymentService().create_payment(
        store=store, user=buyer, order=order, gateway_code="manual"
    )
    PaymentService().capture_payment(payment=payment)  # captures -> confirms the order
    order.refresh_from_db()
    return order, payment


def _return_all(store, buyer, order, **kwargs):
    items = [{"order_item_id": str(oi.id), "quantity": oi.quantity} for oi in order.items.all()]
    rma = ReturnService().create_return(
        store=store, user=buyer, order_id=order.id, items=items, **kwargs
    )
    ReturnService().approve(rma=rma)
    return ReturnService().refund(rma=rma)


def test_refund_returns_to_original_gateway(make_store, make_user, make_variant, store_client):
    store, _owner = make_store()
    buyer = make_user()
    variant = make_variant(store, price="50.00")
    order, payment = _paid_order(store_client, store, buyer, variant, qty=2)
    assert order.status == OrderStatus.CONFIRMED

    rma = _return_all(store, buyer, order)  # default resolution = refund
    assert rma.refund_reference == "gateway:manual"
    payment.refresh_from_db()
    assert payment.status == PaymentStatus.REFUNDED
    # Money went back to the gateway, so the wallet was not credited.
    assert WalletService().balance(store=store, user=buyer) == Decimal("0.00")


def test_store_credit_resolution_always_uses_wallet(
    make_store, make_user, make_variant, store_client
):
    store, _owner = make_store()
    buyer = make_user()
    variant = make_variant(store, price="50.00")
    order, payment = _paid_order(store_client, store, buyer, variant, qty=2)

    rma = _return_all(store, buyer, order, resolution=ReturnResolution.STORE_CREDIT)
    assert rma.refund_reference == "wallet"
    assert WalletService().balance(store=store, user=buyer) == Decimal("100.00")
    payment.refresh_from_db()
    assert payment.status == PaymentStatus.CAPTURED  # gateway untouched


def test_refund_without_payment_falls_back_to_wallet(
    make_store, make_user, make_variant, store_client
):
    store, _owner = make_store()
    buyer = make_user()
    variant = make_variant(store, price="50.00")
    # Confirm directly (no captured payment), mirroring the legacy path.
    client = store_client(buyer, store)
    client.post(
        reverse("v1:cart:item-add"), {"variant_id": str(variant.id), "quantity": 2}, format="json"
    )
    order_data = client.post(reverse("v1:cart:checkout")).json()["data"]
    client.post(reverse("v1:orders:confirm", kwargs={"order_id": order_data["id"]}))
    order = Order.objects.get(id=order_data["id"])

    rma = _return_all(store, buyer, order)
    assert rma.refund_reference == "wallet"
    assert WalletService().balance(store=store, user=buyer) == Decimal("100.00")
