"""Catalog repositories (queries run through tenant-scoped managers)."""

from __future__ import annotations

from apps.catalog.models import Brand, Category, Product, ProductVariant
from apps.core.repositories import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    model = Category


class BrandRepository(BaseRepository[Brand]):
    model = Brand


class ProductRepository(BaseRepository[Product]):
    model = Product

    def with_relations(self):
        return self.get_queryset().select_related("category", "brand")


class ProductVariantRepository(BaseRepository[ProductVariant]):
    model = ProductVariant

    def for_product(self, product_id):
        return self.get_queryset().filter(product_id=product_id)

    def sku_exists(self, *, store, sku: str, exclude_pk: object | None = None) -> bool:
        qs = ProductVariant.all_objects.filter(store=store, sku=sku, is_deleted=False)
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        return qs.exists()
