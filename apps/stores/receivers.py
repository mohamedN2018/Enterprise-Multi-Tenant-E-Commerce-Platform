"""Invalidate the tenant-resolution cache when a store or its settings change.

Connected in :class:`apps.stores.apps.StoresConfig.ready`. Keeps the cached
``resolve_store`` result fresh (a store rename, deactivation or settings tweak
takes effect immediately rather than after the TTL).
"""

from __future__ import annotations

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.stores.models import Store, StoreSettings
from apps.stores.tenancy import store_cache_keys


@receiver(post_save, sender=Store, dispatch_uid="stores.invalidate_store_save")
@receiver(post_delete, sender=Store, dispatch_uid="stores.invalidate_store_delete")
def _invalidate_store(sender, instance, **kwargs) -> None:
    cache.delete_many(store_cache_keys(store_id=instance.id, slug=instance.slug))


@receiver(post_save, sender=StoreSettings, dispatch_uid="stores.invalidate_settings_save")
@receiver(post_delete, sender=StoreSettings, dispatch_uid="stores.invalidate_settings_delete")
def _invalidate_settings(sender, instance, **kwargs) -> None:
    slug = Store.all_objects.filter(pk=instance.store_id).values_list("slug", flat=True).first()
    cache.delete_many(store_cache_keys(store_id=instance.store_id, slug=slug))
