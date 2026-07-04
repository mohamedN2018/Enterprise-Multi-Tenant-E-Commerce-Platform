"""Product image upload / remove endpoint tests."""

from __future__ import annotations

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.catalog.models import Product
from apps.stores.models import StoreRole

pytestmark = pytest.mark.django_db

PRODUCT_LIST = reverse("v1:catalog:product-list")


def _png_bytes() -> bytes:
    """A minimal valid 1x1 PNG so Pillow accepts it as an image."""
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (1, 1), (240, 139, 0)).save(buf, format="PNG")
    return buf.getvalue()


def _make_product(store_client, store, owner) -> str:
    client = store_client(owner, store)
    return client.post(PRODUCT_LIST, {"name": "Widget"}, format="json").json()["data"]["id"]


def test_upload_product_image(store_client, make_store):
    store, owner = make_store()
    client = store_client(owner, store)
    product_id = _make_product(store_client, store, owner)
    url = reverse("v1:catalog:product-image", kwargs={"product_id": product_id})
    upload = SimpleUploadedFile("p.png", _png_bytes(), content_type="image/png")

    resp = client.post(url, {"image": upload}, format="multipart")

    assert resp.status_code == 200
    assert resp.json()["data"]["image"]
    product = Product.objects.get(id=product_id)
    assert product.image.name.startswith("products/")


def test_upload_without_file_rejected(store_client, make_store):
    store, owner = make_store()
    client = store_client(owner, store)
    product_id = _make_product(store_client, store, owner)
    url = reverse("v1:catalog:product-image", kwargs={"product_id": product_id})

    resp = client.post(url, {}, format="multipart")

    assert resp.status_code == 400
    assert resp.json()["error_code"] == "no_image"


def test_remove_product_image(store_client, make_store):
    store, owner = make_store()
    client = store_client(owner, store)
    product_id = _make_product(store_client, store, owner)
    url = reverse("v1:catalog:product-image", kwargs={"product_id": product_id})
    upload = SimpleUploadedFile("p.png", _png_bytes(), content_type="image/png")
    client.post(url, {"image": upload}, format="multipart")

    resp = client.delete(url)

    assert resp.status_code == 200
    assert not Product.objects.get(id=product_id).image


def test_reject_non_image_disguised_as_png(store_client, make_store):
    """A text/HTML payload renamed .png must be rejected (spoofed content-type)."""
    store, owner = make_store()
    client = store_client(owner, store)
    product_id = _make_product(store_client, store, owner)
    url = reverse("v1:catalog:product-image", kwargs={"product_id": product_id})
    fake = SimpleUploadedFile("evil.png", b"<script>alert(1)</script>", content_type="image/png")

    resp = client.post(url, {"image": fake}, format="multipart")

    assert resp.status_code == 400
    assert resp.json()["error_code"] == "invalid_image"
    assert not Product.objects.get(id=product_id).image


def test_reject_unsupported_extension(store_client, make_store):
    store, owner = make_store()
    client = store_client(owner, store)
    product_id = _make_product(store_client, store, owner)
    url = reverse("v1:catalog:product-image", kwargs={"product_id": product_id})
    bad = SimpleUploadedFile("shell.svg", _png_bytes(), content_type="image/svg+xml")

    resp = client.post(url, {"image": bad}, format="multipart")

    assert resp.status_code == 400
    assert resp.json()["error_code"] == "invalid_image"


def test_employee_cannot_upload_image(store_client, make_store, make_user, add_member):
    store, owner = make_store()
    product_id = _make_product(store_client, store, owner)
    employee = make_user()
    add_member(store, employee, StoreRole.EMPLOYEE)
    url = reverse("v1:catalog:product-image", kwargs={"product_id": product_id})
    upload = SimpleUploadedFile("p.png", _png_bytes(), content_type="image/png")

    resp = store_client(employee, store).post(url, {"image": upload}, format="multipart")

    assert resp.status_code == 403
