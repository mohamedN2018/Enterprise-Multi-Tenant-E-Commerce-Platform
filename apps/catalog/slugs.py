"""Per-store unique slug generation."""

from __future__ import annotations

from django.utils.text import slugify


def unique_slug(model, *, store, name: str, instance=None) -> str:
    """Return a store-unique slug derived from ``name`` (ignores soft-deleted rows)."""
    base = slugify(name)[:240] or "item"
    slug = base
    suffix = 1
    qs = model.all_objects.filter(store=store, is_deleted=False)
    if instance is not None and instance.pk:
        qs = qs.exclude(pk=instance.pk)
    while qs.filter(slug=slug).exists():
        suffix += 1
        slug = f"{base}-{suffix}"
    return slug
