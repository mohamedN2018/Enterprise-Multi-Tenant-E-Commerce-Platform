"""Analytics tests (P2.11): event recording via order signals, summary, RBAC, isolation."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.analytics.models import AnalyticsEvent

from .conftest import place_and_confirm

pytestmark = pytest.mark.django_db

EVENTS = reverse("v1:analytics:event-list")
SUMMARY = reverse("v1:analytics:summary")


def test_order_lifecycle_records_events(make_store, buyer_setup, store_client):
    store, owner = make_store()
    client, _buyer, variant = buyer_setup(store, price="50.00")
    place_and_confirm(client, variant, 2)  # subtotal/total 100
    feed = store_client(owner, store).get(EVENTS).json()["data"]
    types = {e["event_type"] for e in feed}
    assert {"order.placed", "order.confirmed"} <= types


def test_summary_aggregates_events_and_orders(make_store, buyer_setup, store_client):
    store, owner = make_store()
    client, _buyer, variant = buyer_setup(store, price="50.00")
    place_and_confirm(client, variant, 2)  # total 100
    summary = store_client(owner, store).get(SUMMARY).json()["data"]
    assert summary["events"]["order.placed"] == 1
    assert summary["events"]["order.confirmed"] == 1
    assert summary["orders"]["count"] == 1
    assert summary["orders"]["confirmed"] == 1
    assert Decimal(summary["orders"]["revenue"]) == Decimal("100.00")


def test_event_feed_filters_by_type(make_store, buyer_setup, store_client):
    store, owner = make_store()
    client, _buyer, variant = buyer_setup(store)
    place_and_confirm(client, variant)
    feed = store_client(owner, store).get(EVENTS, {"event_type": "order.confirmed"}).json()["data"]
    assert feed
    assert all(e["event_type"] == "order.confirmed" for e in feed)


def test_summary_requires_membership(make_store, buyer_setup):
    store, _owner = make_store()
    client, _buyer, _variant = buyer_setup(store)  # buyer is not a store member
    assert client.get(SUMMARY).status_code == 403


def test_employee_can_read_analytics(make_store, make_user, add_member, store_client):
    from apps.stores.models import StoreRole

    store, _owner = make_store()
    employee = make_user()
    add_member(store, employee, StoreRole.EMPLOYEE)
    assert store_client(employee, store).get(SUMMARY).status_code == 200


def test_events_are_store_scoped(make_store, buyer_setup, store_client):
    store_a, owner_a = make_store(name="A")
    store_b, owner_b = make_store(name="B")
    client_a, _buyer, variant_a = buyer_setup(store_a)
    place_and_confirm(client_a, variant_a)
    assert AnalyticsEvent.objects.filter(store=store_a).exists()
    assert AnalyticsEvent.objects.filter(store=store_b).count() == 0
    feed_b = store_client(owner_b, store_b).get(EVENTS).json()["data"]
    assert feed_b == []
