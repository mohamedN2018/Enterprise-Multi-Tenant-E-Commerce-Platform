"""Fraud application service: assess orders + manual review workflow."""

from __future__ import annotations

from django.conf import settings
from django.utils import timezone

from apps.core.exceptions import ConflictError
from apps.core.services import BaseService, atomic
from apps.fraud.engine import RiskEngine
from apps.fraud.models import FraudCheck, FraudDecision, FraudResolution


class FraudService(BaseService):
    @atomic
    def assess(self, *, order) -> FraudCheck:
        """Score an order and record its :class:`FraudCheck` (idempotent per order)."""
        existing = FraudCheck.objects.filter(order=order).first()
        if existing is not None:
            return existing

        cfg = settings.FRAUD
        if not cfg.get("ENABLED", True):
            score, reasons, decision = 0, [], FraudDecision.APPROVE
        else:
            score, reasons = RiskEngine().evaluate(order)
            if score >= int(cfg.get("REJECT_THRESHOLD", 100)):
                decision = FraudDecision.REJECT
            elif score >= int(cfg.get("REVIEW_THRESHOLD", 50)):
                decision = FraudDecision.REVIEW
            else:
                decision = FraudDecision.APPROVE

        resolution = (
            FraudResolution.CLEARED
            if decision == FraudDecision.APPROVE
            else FraudResolution.PENDING
        )
        return FraudCheck.objects.create(
            store=order.store,
            order=order,
            score=score,
            decision=decision,
            resolution=resolution,
            reasons=reasons,
        )

    def is_blocked(self, *, order) -> bool:
        check = FraudCheck.objects.filter(order=order).first()
        return check is not None and check.is_blocking

    @atomic
    def clear(self, *, check: FraudCheck, reviewer) -> FraudCheck:
        if check.resolution != FraudResolution.PENDING:
            raise ConflictError("This check has already been resolved.", code="already_resolved")
        check.resolution = FraudResolution.CLEARED
        check.reviewed_by = reviewer
        check.reviewed_at = timezone.now()
        check.save(update_fields=["resolution", "reviewed_by", "reviewed_at", "updated_at"])
        return check

    @atomic
    def reject(self, *, check: FraudCheck, reviewer) -> FraudCheck:
        if check.resolution != FraudResolution.PENDING:
            raise ConflictError("This check has already been resolved.", code="already_resolved")
        check.resolution = FraudResolution.REJECTED
        check.reviewed_by = reviewer
        check.reviewed_at = timezone.now()
        check.save(update_fields=["resolution", "reviewed_by", "reviewed_at", "updated_at"])
        # Cancel the held order, releasing any stock reservations.
        from apps.orders.services import CheckoutService

        CheckoutService().cancel_order(order=check.order)
        return check
