"""Storefront exposes the product gallery (image cover + images[] with alt)."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.catalog.models import ProductImage

pytestmark = pytest.mark.django_db


def _detail(product):
    url = reverse("v1:storefront:product-detail", kwargs={"product_id": product.id})
    return APIClient().get(url).json()["data"]


def _make_product(active_store, make_product):
    store = active_store()
    product = make_product(
        store,
        name="سماعة",
        name_en="Headset",
        description="د",
        description_en="d",
        slug="headset",
    )
    return store, product


def test_gallery_exposed_with_alt_and_cover(active_store, make_product):
    store, product = _make_product(active_store, make_product)
    ProductImage.objects.create(
        store=store, product=product, image="products/a.png", position=0, alt_text="Front"
    )
    ProductImage.objects.create(
        store=store, product=product, image="products/b.png", position=1, alt_text="Back"
    )

    data = _detail(product)

    assert [img["image"] for img in data["images"]] == [
        "/media/products/a.png",
        "/media/products/b.png",
    ]
    assert [img["alt"] for img in data["images"]] == ["Front", "Back"]
    # Cover = first gallery image.
    assert data["image"] == "/media/products/a.png"


def test_reorder_changes_cover(active_store, make_product):
    store, product = _make_product(active_store, make_product)
    a = ProductImage.objects.create(store=store, product=product, image="products/a.png", position=0)
    ProductImage.objects.create(store=store, product=product, image="products/b.png", position=1)
    # Push A to the back — B becomes the cover.
    a.position = 5
    a.save(update_fields=["position"])

    assert _detail(product)["image"] == "/media/products/b.png"


def test_falls_back_to_legacy_single_image(active_store, make_product):
    store, product = _make_product(active_store, make_product)
    product.image = "products/legacy.png"
    product.save(update_fields=["image"])

    data = _detail(product)

    assert data["image"] == "/media/products/legacy.png"
    assert data["images"] == [{"image": "/media/products/legacy.png", "alt": ""}]


def test_no_images_returns_empty_list(active_store, make_product):
    _store, product = _make_product(active_store, make_product)
    data = _detail(product)
    assert data["image"] is None
    assert data["images"] == []
