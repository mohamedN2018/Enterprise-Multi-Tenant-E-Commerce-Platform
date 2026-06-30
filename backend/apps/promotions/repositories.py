"""Promotions repositories (tenant-scoped)."""

from __future__ import annotations

from apps.core.repositories import BaseRepository
from apps.promotions.models import Coupon


class CouponRepository(BaseRepository[Coupon]):
    model = Coupon

    def code_exists(self, *, store, code: str, exclude_pk=None) -> bool:
        qs = Coupon.all_objects.filter(store=store, code=code, is_deleted=False)
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        return qs.exists()
