"""Reviews & ratings tests (E1): purchase-gated create, moderation, votes, summary."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.reviews.models import Review
from apps.stores.models import StoreRole

from .conftest import buy_and_deliver

pytestmark = pytest.mark.django_db

REVIEWS = reverse("v1:reviews:list")
SUMMARY = reverse("v1:reviews:summary")


def _create(client, product, *, rating=5, title="", body=""):
    return client.post(
        REVIEWS,
        {"product_id": str(product.id), "rating": rating, "title": title, "body": body},
        format="json",
    )


def _approve(owner_client, review_id):
    return owner_client.post(reverse("v1:reviews:approve", kwargs={"review_id": review_id}))


def _buyer_who_received(store_client, make_user, store, variant):
    """A client whose user has a DELIVERED order for `variant` — eligible to review."""
    client = store_client(make_user(), store)
    buy_and_deliver(client, variant)
    return client


def test_delivered_buyer_review_is_pending_and_verified(
    make_store, make_user, make_variant, store_client
):
    store, _owner = make_store()
    variant = make_variant(store)
    client = _buyer_who_received(store_client, make_user, store, variant)
    data = _create(client, variant.product).json()["data"]
    assert data["status"] == "pending"
    assert data["is_verified_purchase"] is True


def test_cannot_review_without_receiving(make_store, make_user, make_variant, store_client):
    store, _owner = make_store()
    variant = make_variant(store)
    # Buyer never purchased/received the product → review is rejected.
    resp = _create(store_client(make_user(), store), variant.product)
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "not_purchased"


def test_one_review_per_product(make_store, make_user, make_variant, store_client):
    store, _owner = make_store()
    variant = make_variant(store)
    client = _buyer_who_received(store_client, make_user, store, variant)
    assert _create(client, variant.product).status_code == 201
    dup = _create(client, variant.product)
    assert dup.status_code == 409
    assert dup.json()["error_code"] == "already_reviewed"


def test_rating_out_of_range_rejected(make_store, make_user, make_variant, store_client):
    store, _owner = make_store()
    variant = make_variant(store)
    client = _buyer_who_received(store_client, make_user, store, variant)
    assert _create(client, variant.product, rating=6).status_code == 400


def test_approved_reviews_show_in_public_list(make_store, make_user, make_variant, store_client):
    store, owner = make_store()
    variant = make_variant(store)
    buyer_client = _buyer_who_received(store_client, make_user, store, variant)
    product = variant.product
    review_id = _create(buyer_client, product).json()["data"]["id"]
    # Pending review is not public.
    assert buyer_client.get(REVIEWS, {"product": str(product.id)}).json()["data"] == []
    assert _approve(store_client(owner, store), review_id).status_code == 200
    listed = buyer_client.get(REVIEWS, {"product": str(product.id)}).json()["data"]
    assert [r["id"] for r in listed] == [review_id]


def test_only_owner_can_edit(make_store, make_user, make_variant, store_client):
    store, _owner = make_store()
    variant = make_variant(store)
    buyer_client = _buyer_who_received(store_client, make_user, store, variant)
    review_id = _create(buyer_client, variant.product).json()["data"]["id"]
    other = store_client(make_user(), store)
    resp = other.patch(
        reverse("v1:reviews:detail", kwargs={"review_id": review_id}), {"rating": 1}, format="json"
    )
    assert resp.status_code == 404


def test_helpful_vote_is_counted_and_idempotent(make_store, make_user, make_variant, store_client):
    store, owner = make_store()
    variant = make_variant(store)
    buyer_client = _buyer_who_received(store_client, make_user, store, variant)
    review_id = _create(buyer_client, variant.product).json()["data"]["id"]
    _approve(store_client(owner, store), review_id)
    voter = store_client(make_user(), store)
    url = reverse("v1:reviews:vote", kwargs={"review_id": review_id})
    assert voter.post(url, {"is_helpful": True}, format="json").json()["data"]["helpful_count"] == 1
    # Voting again does not double-count.
    assert voter.post(url, {"is_helpful": True}, format="json").json()["data"]["helpful_count"] == 1


def test_summary_aggregates_approved_ratings(make_store, make_user, make_variant, store_client):
    store, owner = make_store()
    variant = make_variant(store)
    product = variant.product
    owner_client = store_client(owner, store)
    for rating in (4, 2):
        client = _buyer_who_received(store_client, make_user, store, variant)
        review_id = _create(client, product, rating=rating).json()["data"]["id"]
        _approve(owner_client, review_id)
    summary = owner_client.get(SUMMARY, {"product": str(product.id)}).json()["data"]
    assert summary["count"] == 2
    assert summary["average_rating"] == 3.0
    assert summary["distribution"]["4"] == 1
    assert summary["distribution"]["2"] == 1


def test_employee_cannot_moderate(make_store, make_user, add_member, make_variant, store_client):
    store, owner = make_store()
    variant = make_variant(store)
    buyer_client = _buyer_who_received(store_client, make_user, store, variant)
    review_id = _create(buyer_client, variant.product).json()["data"]["id"]
    employee = make_user()
    add_member(store, employee, StoreRole.EMPLOYEE)
    url = reverse("v1:reviews:approve", kwargs={"review_id": review_id})
    assert store_client(employee, store).post(url).status_code == 403
    assert store_client(owner, store).post(url).status_code == 200


def test_reviews_are_store_scoped(make_store, make_user, make_variant):
    store_a, _owner_a = make_store(name="A")
    store_b, _owner_b = make_store(name="B")
    product_a = make_variant(store_a).product
    Review.objects.create(store=store_a, product=product_a, user=make_user(), rating=5)
    assert Review.objects.filter(store=store_a).count() == 1
    assert Review.objects.filter(store=store_b).count() == 0
