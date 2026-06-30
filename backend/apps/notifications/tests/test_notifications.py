"""Notification tests (P2.11): order-lifecycle inbox, read state, prefs, email."""

from __future__ import annotations

import pytest
from django.urls import reverse

from .conftest import place_order

pytestmark = pytest.mark.django_db

LIST = reverse("v1:notifications:list")
UNREAD = reverse("v1:notifications:unread-count")
READ_ALL = reverse("v1:notifications:read-all")
PREFS = reverse("v1:notifications:preferences")


def test_order_placed_creates_buyer_notification(make_store, buyer_setup):
    store, _owner = make_store()
    client, _buyer, variant = buyer_setup(store)
    place_order(client, variant)
    data = client.get(LIST).json()["data"]
    assert len(data) == 1
    assert data[0]["event_type"] == "order.placed"
    assert data[0]["is_read"] is False


def test_order_confirmed_adds_notification(make_store, buyer_setup):
    store, _owner = make_store()
    client, _buyer, variant = buyer_setup(store)
    order = place_order(client, variant).json()["data"]
    client.post(reverse("v1:orders:confirm", kwargs={"order_id": order["id"]}))
    types = {n["event_type"] for n in client.get(LIST).json()["data"]}
    assert {"order.placed", "order.confirmed"} <= types


def test_unread_count_and_mark_read(make_store, buyer_setup):
    store, _owner = make_store()
    client, _buyer, variant = buyer_setup(store)
    place_order(client, variant)
    assert client.get(UNREAD).json()["data"]["unread"] == 1
    notification_id = client.get(LIST).json()["data"][0]["id"]
    resp = client.post(
        reverse("v1:notifications:read", kwargs={"notification_id": notification_id})
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["is_read"] is True
    assert client.get(UNREAD).json()["data"]["unread"] == 0


def test_mark_all_read(make_store, buyer_setup):
    store, _owner = make_store()
    client, _buyer, variant = buyer_setup(store)
    place_order(client, variant)
    place_order(client, variant)
    assert client.get(UNREAD).json()["data"]["unread"] == 2
    assert client.post(READ_ALL).json()["data"]["updated"] == 2
    assert client.get(UNREAD).json()["data"]["unread"] == 0


def test_preferences_default_and_update(make_store, buyer_setup):
    store, _owner = make_store()
    client, _buyer, _variant = buyer_setup(store)
    prefs = client.get(PREFS).json()["data"]
    assert prefs["in_app_enabled"] is True
    assert prefs["email_enabled"] is False
    updated = client.put(PREFS, {"email_enabled": True}, format="json").json()["data"]
    assert updated["email_enabled"] is True


def test_no_email_by_default(make_store, buyer_setup, mailoutbox):
    store, _owner = make_store()
    client, _buyer, variant = buyer_setup(store)
    place_order(client, variant)
    assert mailoutbox == []  # in-app only
    assert len(client.get(LIST).json()["data"]) == 1


def test_email_sent_when_enabled(make_store, buyer_setup, mailoutbox):
    store, _owner = make_store()
    client, buyer, variant = buyer_setup(store)
    client.put(PREFS, {"email_enabled": True}, format="json")
    place_order(client, variant)
    assert len(mailoutbox) == 1
    assert "placed" in mailoutbox[0].subject.lower()
    assert mailoutbox[0].to == [buyer.email]


def test_notifications_are_recipient_scoped(make_store, buyer_setup):
    store, _owner = make_store()
    client_a, _buyer_a, variant_a = buyer_setup(store)
    client_b, _buyer_b, _variant_b = buyer_setup(store)
    place_order(client_a, variant_a)
    assert len(client_a.get(LIST).json()["data"]) == 1
    assert len(client_b.get(LIST).json()["data"]) == 0
