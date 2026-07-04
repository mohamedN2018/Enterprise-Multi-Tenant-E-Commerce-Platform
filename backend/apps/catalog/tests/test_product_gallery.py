"""Product gallery (multiple images) endpoint tests."""

from __future__ import annotations

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.catalog.models import Product, ProductImage
from apps.stores.models import StoreRole

pytestmark = pytest.mark.django_db

PRODUCT_LIST = reverse("v1:catalog:product-list")


def _png(name="p.png") -> SimpleUploadedFile:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (2, 2), (240, 139, 0)).save(buf, format="PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


def _product(store_client, store, owner) -> str:
    return store_client(owner, store).post(
        PRODUCT_LIST, {"name": "Widget"}, format="json"
    ).json()["data"]["id"]


def _gallery_url(product_id):
    return reverse("v1:catalog:product-gallery", kwargs={"product_id": product_id})


def test_add_images_appends_in_order(store_client, make_store):
    store, owner = make_store()
    client = store_client(owner, store)
    product_id = _product(store_client, store, owner)
    url = _gallery_url(product_id)

    first = client.post(url, {"image": _png("a.png")}, format="multipart")
    second = client.post(url, {"image": _png("b.png")}, format="multipart")

    assert first.status_code == 201 and second.status_code == 201
    listing = client.get(url).json()["data"]
    assert len(listing) == 2
    assert listing[0]["position"] < listing[1]["position"]


def test_primary_image_is_first_gallery_image(store_client, make_store):
    store, owner = make_store()
    client = store_client(owner, store)
    product_id = _product(store_client, store, owner)
    client.post(_gallery_url(product_id), {"image": _png()}, format="multipart")

    detail = client.get(
        reverse("v1:catalog:product-detail", kwargs={"product_id": product_id})
    ).json()["data"]
    assert detail["image"] is not None
    assert detail["image"] == detail["images"][0]["image"]


def test_reorder_gallery(store_client, make_store):
    store, owner = make_store()
    client = store_client(owner, store)
    product_id = _product(store_client, store, owner)
    url = _gallery_url(product_id)
    a = client.post(url, {"image": _png("a.png")}, format="multipart").json()["data"]["id"]
    b = client.post(url, {"image": _png("b.png")}, format="multipart").json()["data"]["id"]

    resp = client.post(
        reverse("v1:catalog:product-gallery-reorder", kwargs={"product_id": product_id}),
        {"order": [b, a]},
        format="json",
    )
    assert resp.status_code == 200
    assert [img["id"] for img in resp.json()["data"]] == [b, a]


def test_add_image_with_alt_text(store_client, make_store):
    store, owner = make_store()
    client = store_client(owner, store)
    product_id = _product(store_client, store, owner)
    resp = client.post(
        _gallery_url(product_id), {"image": _png(), "alt_text": "Front view"}, format="multipart"
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["alt_text"] == "Front view"


def test_patch_alt_text(store_client, make_store):
    store, owner = make_store()
    client = store_client(owner, store)
    product_id = _product(store_client, store, owner)
    img_id = client.post(
        _gallery_url(product_id), {"image": _png()}, format="multipart"
    ).json()["data"]["id"]
    url = reverse(
        "v1:catalog:product-gallery-item", kwargs={"product_id": product_id, "image_id": img_id}
    )

    resp = client.patch(url, {"alt_text": "Side angle"}, format="json")

    assert resp.status_code == 200
    assert resp.json()["data"]["alt_text"] == "Side angle"


def test_delete_gallery_image(store_client, make_store):
    store, owner = make_store()
    client = store_client(owner, store)
    product_id = _product(store_client, store, owner)
    img_id = client.post(
        _gallery_url(product_id), {"image": _png()}, format="multipart"
    ).json()["data"]["id"]

    resp = client.delete(
        reverse("v1:catalog:product-gallery-item", kwargs={"product_id": product_id, "image_id": img_id})
    )
    assert resp.status_code == 200
    assert client.get(_gallery_url(product_id)).json()["data"] == []


def test_gallery_limit_enforced(store_client, make_store):
    store, owner = make_store()
    client = store_client(owner, store)
    product_id = _product(store_client, store, owner)
    product = Product.objects.get(id=product_id)
    # Fill to the cap directly, then the API must refuse one more.
    for i in range(10):
        ProductImage.objects.create(store=store, product=product, position=i, image=f"products/x{i}.png")

    resp = client.post(_gallery_url(product_id), {"image": _png()}, format="multipart")
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "gallery_full"


def test_reject_non_image(store_client, make_store):
    store, owner = make_store()
    client = store_client(owner, store)
    product_id = _product(store_client, store, owner)
    bad = SimpleUploadedFile("x.png", b"not-an-image", content_type="image/png")

    resp = client.post(_gallery_url(product_id), {"image": bad}, format="multipart")
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "invalid_image"


def test_employee_cannot_add_image(store_client, make_store, make_user, add_member):
    store, owner = make_store()
    product_id = _product(store_client, store, owner)
    employee = make_user()
    add_member(store, employee, StoreRole.EMPLOYEE)

    resp = store_client(employee, store).post(
        _gallery_url(product_id), {"image": _png()}, format="multipart"
    )
    assert resp.status_code == 403


def test_gallery_is_store_scoped(store_client, make_store):
    store_a, owner_a = make_store()
    store_b, owner_b = make_store()
    product_a = _product(store_client, store_a, owner_a)
    # Owner B, acting in store B, cannot touch store A's product gallery.
    resp = store_client(owner_b, store_b).get(_gallery_url(product_a))
    assert resp.status_code == 404
