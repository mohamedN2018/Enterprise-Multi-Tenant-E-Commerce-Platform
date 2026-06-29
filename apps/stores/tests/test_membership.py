"""Membership management + RBAC tests."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.stores.models import StoreMembership, StoreRole

pytestmark = pytest.mark.django_db


def _members_url(store_id):
    return reverse("v1:stores:member-list", kwargs={"store_id": store_id})


def _member_url(store_id, member_id):
    return reverse("v1:stores:member-detail", kwargs={"store_id": store_id, "member_id": member_id})


def test_owner_adds_member_by_email(client_for, make_store, make_user):
    store, owner = make_store()
    invitee = make_user(email="invitee@example.com")
    resp = client_for(owner).post(
        _members_url(store.id), {"email": invitee.email, "role": "manager"}, format="json"
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["role"] == "manager"
    assert StoreMembership.objects.filter(
        store=store, user=invitee, role=StoreRole.MANAGER, is_active=True
    ).exists()


def test_add_member_unknown_email(client_for, make_store):
    store, owner = make_store()
    resp = client_for(owner).post(
        _members_url(store.id), {"email": "ghost@example.com", "role": "employee"}, format="json"
    )
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "user_not_found"


def test_add_member_invalid_role(client_for, make_store, make_user):
    store, owner = make_store()
    invitee = make_user()
    resp = client_for(owner).post(
        _members_url(store.id), {"email": invitee.email, "role": "owner"}, format="json"
    )
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "invalid_role"


def test_add_duplicate_member_conflict(client_for, make_store, make_user):
    store, owner = make_store()
    invitee = make_user()
    url = _members_url(store.id)
    client = client_for(owner)
    client.post(url, {"email": invitee.email, "role": "employee"}, format="json")
    dupe = client.post(url, {"email": invitee.email, "role": "employee"}, format="json")
    assert dupe.status_code == 409
    assert dupe.json()["error_code"] == "already_member"


def test_manager_can_add_but_not_change_roles(client_for, make_store, make_user):
    store, owner = make_store()
    manager = make_user()
    StoreMembership.objects.create(
        store=store, user=manager, role=StoreRole.MANAGER, is_active=True
    )
    employee = make_user()
    m_client = client_for(manager)
    # Manager may add members.
    add = m_client.post(
        _members_url(store.id), {"email": employee.email, "role": "employee"}, format="json"
    )
    assert add.status_code == 201
    membership_id = add.json()["data"]["id"]
    # Manager may NOT change roles (owner-only).
    change = m_client.patch(
        _member_url(store.id, membership_id), {"role": "manager"}, format="json"
    )
    assert change.status_code == 403


def test_owner_changes_role(client_for, make_store, make_user):
    store, owner = make_store()
    employee = make_user()
    membership = StoreMembership.objects.create(
        store=store, user=employee, role=StoreRole.EMPLOYEE, is_active=True
    )
    resp = client_for(owner).patch(
        _member_url(store.id, membership.id), {"role": "manager"}, format="json"
    )
    assert resp.status_code == 200
    membership.refresh_from_db()
    assert membership.role == StoreRole.MANAGER


def test_cannot_change_owner_role(client_for, make_store):
    store, owner = make_store()
    owner_membership = StoreMembership.objects.get(store=store, user=owner)
    resp = client_for(owner).patch(
        _member_url(store.id, owner_membership.id), {"role": "manager"}, format="json"
    )
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "owner_immutable"


def test_owner_removes_member(client_for, make_store, make_user):
    store, owner = make_store()
    employee = make_user()
    membership = StoreMembership.objects.create(
        store=store, user=employee, role=StoreRole.EMPLOYEE, is_active=True
    )
    resp = client_for(owner).delete(_member_url(store.id, membership.id))
    assert resp.status_code == 200
    assert not StoreMembership.objects.filter(id=membership.id).exists()


def test_cannot_remove_owner(client_for, make_store):
    store, owner = make_store()
    owner_membership = StoreMembership.objects.get(store=store, user=owner)
    resp = client_for(owner).delete(_member_url(store.id, owner_membership.id))
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "owner_immutable"


def test_non_member_cannot_list_members(client_for, make_store, make_user):
    store, _owner = make_store()
    outsider = make_user()
    resp = client_for(outsider).get(_members_url(store.id))
    assert resp.status_code == 403
