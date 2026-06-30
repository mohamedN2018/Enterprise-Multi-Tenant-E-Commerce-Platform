"""Generic repository — a thin, reusable data-access abstraction.

The repository isolates the service layer from ORM specifics, centralises query
construction, and makes data access trivially mockable in unit tests. Domain
repositories subclass :class:`BaseRepository`, set ``model`` and add
query methods expressing domain intent (e.g. ``active_for_store``).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Generic, TypeVar

from django.db import models
from django.db.models import QuerySet

M = TypeVar("M", bound=models.Model)


class BaseRepository(Generic[M]):
    model: type[M]

    def __init__(self, model: type[M] | None = None) -> None:
        if model is not None:
            self.model = model
        if not getattr(self, "model", None):
            raise ValueError(f"{type(self).__name__} requires a `model`.")

    # --- Read ---
    def get_queryset(self) -> QuerySet[M]:
        return self.model._default_manager.all()

    def all(self) -> QuerySet[M]:
        return self.get_queryset()

    def filter(self, **kwargs: Any) -> QuerySet[M]:
        return self.get_queryset().filter(**kwargs)

    def get(self, **kwargs: Any) -> M:
        return self.get_queryset().get(**kwargs)

    def get_by_id(self, pk: Any) -> M:
        return self.get_queryset().get(pk=pk)

    def get_or_none(self, **kwargs: Any) -> M | None:
        return self.get_queryset().filter(**kwargs).first()

    def exists(self, **kwargs: Any) -> bool:
        return self.get_queryset().filter(**kwargs).exists()

    def count(self, **kwargs: Any) -> int:
        qs = self.get_queryset()
        return qs.filter(**kwargs).count() if kwargs else qs.count()

    # --- Write ---
    def create(self, **kwargs: Any) -> M:
        return self.model._default_manager.create(**kwargs)

    def bulk_create(self, objs: Iterable[M], **kwargs: Any) -> list[M]:
        return self.model._default_manager.bulk_create(list(objs), **kwargs)

    def update(self, instance: M, **fields: Any) -> M:
        for name, value in fields.items():
            setattr(instance, name, value)
        instance.save(update_fields=list(fields.keys()) or None)
        return instance

    def delete(self, instance: M, *, hard: bool = False) -> None:
        # Honours soft-delete when the model supports it.
        try:
            instance.delete(hard=hard)  # type: ignore[call-arg]
        except TypeError:
            instance.delete()
