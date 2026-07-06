"""Platform (super-admin) API + per-seller / per-store limit tests."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.stores.models import Store, StoreStatus

pytestmark = pytest.mark.django_db

STORE_LIST = reverse("v1:stores:store-list")
PLATFORM_STORES = reverse("v1:platform:store-list")
PLATFORM_SELLERS = reverse("v1:platform:seller-list")


def _member_url(store_id):
    return reverse("v1:stores:member-list", kwargs={"store_id": store_id})


def _platform_store(store_id):
    return reverse("v1:platform:store-detail", kwargs={"store_id": store_id})


def _platform_seller(user_id):
    return reverse("v1:platform:seller-detail", kwargs={"user_id": user_id})


def _limit_requests(store_id):
    return reverse("v1:stores:limit-requests", kwargs={"store_id": store_id})


PLATFORM_REQUESTS = reverse("v1:platform:request-list")


def _approve(request_id):
    return reverse("v1:platform:request-approve", kwargs={"request_id": request_id})


def _reject(request_id):
    return reverse("v1:platform:request-reject", kwargs={"request_id": request_id})


@pytest.fixture
def superadmin(make_user):
    admin = make_user(email="root@example.com")
    admin.is_superuser = True
    admin.is_staff = True
    admin.save(update_fields=["is_superuser", "is_staff"])
    return admin


# --- Store limit ------------------------------------------------------------
def test_store_limit_blocks_second_store(client_for, make_user):
    seller = make_user()
    client = client_for(seller)
    assert client.post(STORE_LIST, {"name": "First"}, format="json").status_code == 201
    resp = client.post(STORE_LIST, {"name": "Second"}, format="json")
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "store_limit_reached"


def test_admin_raises_store_limit_then_seller_creates_second(client_for, make_user, superadmin):
    seller = make_user()
    client_for(seller).post(STORE_LIST, {"name": "First"}, format="json")

    resp = client_for(superadmin).patch(
        _platform_seller(seller.id), {"max_stores": 2}, format="json"
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["max_stores"] == 2

    # force_authenticate reuses the in-memory object; reload so it reflects the
    # DB change (a real JWT request loads the user fresh each time).
    seller.refresh_from_db()
    second = client_for(seller).post(STORE_LIST, {"name": "Second"}, format="json")
    assert second.status_code == 201


# --- Admin creates a store for a contracted seller --------------------------
def test_admin_creates_store_for_seller(client_for, make_user, superadmin):
    seller = make_user(email="seller@example.com")
    resp = client_for(superadmin).post(
        PLATFORM_STORES,
        {"owner_email": "seller@example.com", "name": "Assigned Shop"},
        format="json",
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["owner_email"] == "seller@example.com"

    store = Store.objects.get(id=data["id"])
    assert store.owner_id == seller.id
    assert store.status == StoreStatus.ACTIVE  # admin-created stores go live

    # The seller now owns it and sees it in their own store list.
    mine = client_for(seller).get(STORE_LIST)
    assert mine.json()["meta"]["pagination"]["count"] == 1
    assert mine.json()["data"][0]["id"] == str(store.id)


def test_admin_create_for_unknown_email_fails(client_for, superadmin):
    resp = client_for(superadmin).post(
        PLATFORM_STORES, {"owner_email": "ghost@nowhere.com", "name": "X"}, format="json"
    )
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "user_not_found"


# --- Create seller account --------------------------------------------------
def test_admin_creates_seller_account(client_for, superadmin):
    resp = client_for(superadmin).post(
        PLATFORM_SELLERS,
        {"email": "newseller@example.com", "password": "StrongPass!2026"},
        format="json",
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["email"] == "newseller@example.com"
    assert data["max_stores"] == 1  # one store per seller by default
    assert data["store_count"] == 0

    user = User.objects.get(email="newseller@example.com")
    assert user.is_active and user.is_verified and not user.is_superuser


def test_created_seller_gets_default_store_and_can_log_in(client_for, superadmin):
    resp = client_for(superadmin).post(
        PLATFORM_SELLERS,
        {"email": "shopkeeper@example.com", "password": "StrongPass!2026", "store_name": "متجري"},
        format="json",
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["store_count"] == 1
    store = Store.objects.get(owner__email="shopkeeper@example.com")
    assert store.status == StoreStatus.ACTIVE

    # The seller may sign in immediately (admin-verified) and is at their cap.
    seller = User.objects.get(email="shopkeeper@example.com")
    second = client_for(seller).post(STORE_LIST, {"name": "Another"}, format="json")
    assert second.status_code == 400
    assert second.json()["error_code"] == "store_limit_reached"


def test_create_seller_duplicate_email_rejected(client_for, superadmin, make_user):
    make_user(email="taken@example.com")
    resp = client_for(superadmin).post(
        PLATFORM_SELLERS,
        {"email": "taken@example.com", "password": "StrongPass!2026"},
        format="json",
    )
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "email_taken"


def test_create_seller_requires_superuser(client_for, make_user):
    resp = client_for(make_user()).post(
        PLATFORM_SELLERS,
        {"email": "x@example.com", "password": "StrongPass!2026"},
        format="json",
    )
    assert resp.status_code == 403


# --- Access control ---------------------------------------------------------
def test_platform_requires_superuser(client_for, make_user):
    seller = make_user()
    assert client_for(seller).get(PLATFORM_STORES).status_code == 403
    assert client_for(seller).get(PLATFORM_SELLERS).status_code == 403


def test_platform_lists_all_stores(client_for, make_store, superadmin):
    make_store(name="One")
    make_store(name="Two")  # different owner
    resp = client_for(superadmin).get(PLATFORM_STORES)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 2


# --- Employee limit ---------------------------------------------------------
def test_employee_limit_enforced(client_for, make_store, make_user):
    store, owner = make_store()
    make_user(email="e1@example.com")
    make_user(email="e2@example.com")
    make_user(email="m@example.com")
    owner_client = client_for(owner)

    ok = owner_client.post(
        _member_url(store.id), {"email": "e1@example.com", "role": "employee"}, format="json"
    )
    assert ok.status_code == 201

    blocked = owner_client.post(
        _member_url(store.id), {"email": "e2@example.com", "role": "employee"}, format="json"
    )
    assert blocked.status_code == 400
    assert blocked.json()["error_code"] == "employee_limit_reached"

    # Managers are not capped by the employee limit.
    mgr = owner_client.post(
        _member_url(store.id), {"email": "m@example.com", "role": "manager"}, format="json"
    )
    assert mgr.status_code == 201


def test_admin_raises_employee_limit(client_for, make_store, make_user, superadmin):
    store, owner = make_store()
    make_user(email="e1@example.com")
    make_user(email="e2@example.com")

    resp = client_for(superadmin).patch(
        _platform_store(store.id), {"max_employees": 2}, format="json"
    )
    assert resp.status_code == 200
    store.settings.refresh_from_db()
    assert store.settings.max_employees == 2

    owner_client = client_for(owner)
    assert (
        owner_client.post(
            _member_url(store.id), {"email": "e1@example.com", "role": "employee"}, format="json"
        ).status_code
        == 201
    )
    assert (
        owner_client.post(
            _member_url(store.id), {"email": "e2@example.com", "role": "employee"}, format="json"
        ).status_code
        == 201
    )


# --- Limit-increase requests ------------------------------------------------
def test_owner_requests_more_employees(client_for, make_store):
    store, owner = make_store()
    resp = client_for(owner).post(
        _limit_requests(store.id), {"requested_limit": 3, "note": "hiring"}, format="json"
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["status"] == "pending"
    assert resp.json()["data"]["requested_limit"] == 3

    listed = client_for(owner).get(_limit_requests(store.id))
    assert len(listed.json()["data"]) == 1


def test_request_must_exceed_current_limit(client_for, make_store):
    store, owner = make_store()  # max_employees defaults to 1
    resp = client_for(owner).post(_limit_requests(store.id), {"requested_limit": 1}, format="json")
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "invalid_limit"


def test_duplicate_pending_request_conflicts(client_for, make_store):
    store, owner = make_store()
    client_for(owner).post(_limit_requests(store.id), {"requested_limit": 2}, format="json")
    dupe = client_for(owner).post(_limit_requests(store.id), {"requested_limit": 3}, format="json")
    assert dupe.status_code == 409
    assert dupe.json()["error_code"] == "request_pending"


def test_non_owner_cannot_request(client_for, make_store, make_user):
    from apps.stores.models import StoreMembership, StoreRole

    store, _owner = make_store()
    manager = make_user()
    StoreMembership.objects.create(store=store, user=manager, role=StoreRole.MANAGER, is_active=True)
    resp = client_for(manager).post(_limit_requests(store.id), {"requested_limit": 3}, format="json")
    assert resp.status_code == 403


def test_admin_approves_request_raises_cap(client_for, make_store, make_user, superadmin):
    store, owner = make_store()
    make_user(email="e1@example.com")
    make_user(email="e2@example.com")
    req = client_for(owner).post(_limit_requests(store.id), {"requested_limit": 2}, format="json")
    req_id = req.json()["data"]["id"]

    # Admin sees it and approves.
    pending = client_for(superadmin).get(PLATFORM_REQUESTS + "?status=pending")
    assert any(r["id"] == req_id for r in pending.json()["data"])
    approved = client_for(superadmin).post(_approve(req_id))
    assert approved.status_code == 200
    assert approved.json()["data"]["status"] == "approved"

    store.settings.refresh_from_db()
    assert store.settings.max_employees == 2

    # Owner can now add two employees.
    oc = client_for(owner)
    assert oc.post(_member_url(store.id), {"email": "e1@example.com", "role": "employee"}, format="json").status_code == 201
    assert oc.post(_member_url(store.id), {"email": "e2@example.com", "role": "employee"}, format="json").status_code == 201


def test_admin_rejects_request_keeps_cap(client_for, make_store, superadmin):
    store, owner = make_store()
    req = client_for(owner).post(_limit_requests(store.id), {"requested_limit": 5}, format="json")
    req_id = req.json()["data"]["id"]
    resp = client_for(superadmin).post(_reject(req_id))
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "rejected"
    store.settings.refresh_from_db()
    assert store.settings.max_employees == 1


def test_requests_list_requires_superuser(client_for, make_user):
    assert client_for(make_user()).get(PLATFORM_REQUESTS).status_code == 403


# --- Super-admin acts as owner of any store (god-mode) ----------------------
def test_superuser_manages_any_store_as_owner(client_for, make_store, superadmin):
    store, _owner = make_store()  # superadmin is NOT a member
    admin = client_for(superadmin)

    settings_url = reverse("v1:stores:store-settings", kwargs={"store_id": store.id})
    assert admin.get(settings_url).status_code == 200
    assert admin.patch(settings_url, {"low_stock_threshold": 3}, format="json").status_code == 200

    members_url = reverse("v1:stores:member-list", kwargs={"store_id": store.id})
    assert admin.get(members_url).status_code == 200

    detail = reverse("v1:stores:store-detail", kwargs={"store_id": store.id})
    assert admin.patch(detail, {"status": "active"}, format="json").status_code == 200


def test_superuser_reads_store_scoped_catalog(client_for, make_store, superadmin):
    store, _owner = make_store()
    resp = client_for(superadmin).get("/api/v1/catalog/products/", HTTP_X_STORE_ID=str(store.id))
    assert resp.status_code == 200


def test_non_member_non_superuser_still_blocked(client_for, make_store, make_user):
    store, _owner = make_store()
    outsider = make_user()
    settings_url = reverse("v1:stores:store-settings", kwargs={"store_id": store.id})
    assert client_for(outsider).get(settings_url).status_code == 403


def test_seller_requests_more_stores_and_admin_approves(client_for, make_store, make_user, superadmin):
    store, owner = make_store()  # owner.max_stores defaults to 1
    url = reverse("v1:stores:user-limit-requests")
    req = client_for(owner).post(url, {"requested_limit": 3, "note": "expanding"}, format="json")
    assert req.status_code == 201
    assert req.json()["data"]["kind"] == "stores"
    req_id = req.json()["data"]["id"]

    client_for(superadmin).post(_approve(req_id))
    owner.refresh_from_db()
    assert owner.max_stores == 3

    # Owner can now self-create additional stores up to the new cap.
    second = client_for(owner).post(STORE_LIST, {"name": "Second"}, format="json")
    assert second.status_code == 201
