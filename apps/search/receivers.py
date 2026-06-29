"""Cache-invalidation receivers: bump a store's search version on catalog writes.

Connected in :class:`apps.search.apps.SearchConfig.ready`. A single version bump
invalidates every cached search query for that store, so stale results never
outlive a product or variant change.
"""

from __future__ import annotations

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.catalog.models import Product, ProductVariant
from apps.search.services import ProductSearchService


@receiver(post_save, sender=Product, dispatch_uid="search.invalidate_product_save")
@receiver(post_delete, sender=Product, dispatch_uid="search.invalidate_product_delete")
def _invalidate_for_product(sender, instance, **kwargs) -> None:
    if instance.store_id:
        ProductSearchService.invalidate(store=instance.store)


@receiver(post_save, sender=ProductVariant, dispatch_uid="search.invalidate_variant_save")
@receiver(post_delete, sender=ProductVariant, dispatch_uid="search.invalidate_variant_delete")
def _invalidate_for_variant(sender, instance, **kwargs) -> None:
    if instance.store_id:
        ProductSearchService.invalidate(store=instance.store)
