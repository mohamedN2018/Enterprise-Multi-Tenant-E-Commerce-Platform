"""Pricing repositories (tenant-scoped)."""

from __future__ import annotations

from apps.core.repositories import BaseRepository
from apps.pricing.models import CustomerGroup, PriceRule


class CustomerGroupRepository(BaseRepository[CustomerGroup]):
    model = CustomerGroup

    def code_exists(self, *, store, code: str, exclude_pk=None) -> bool:
        qs = CustomerGroup.all_objects.filter(store=store, code=code, is_deleted=False)
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        return qs.exists()


class PriceRuleRepository(BaseRepository[PriceRule]):
    model = PriceRule
