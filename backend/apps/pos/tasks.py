"""Outbound stock push to a linked cashier (platform -> POS).

Runs in a Celery worker so an external webhook never blocks a checkout. Uses the
stdlib ``urllib`` (no extra dependency) with a short timeout, and signs the body
with the connection's secret so the cashier can trust it. Best-effort: transport
errors are logged and swallowed — the cashier can always re-pull via GET /stock/.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request

from celery import shared_task

from apps.pos import keys
from apps.pos.client import USER_AGENT
from apps.pos.models import PosConnection
from apps.pos.services import PosService

logger = logging.getLogger(__name__)

WEBHOOK_TIMEOUT = 5  # seconds


@shared_task(name="pos.push_stock_update", max_retries=3, default_retry_delay=30, bind=True)
def push_stock_update(self, connection_id: str, sku: str) -> str:
    connection = (
        PosConnection.all_objects.filter(id=connection_id, is_active=True, is_deleted=False)
        .select_related("store")
        .first()
    )
    if connection is None or not connection.webhook_url:
        return "skipped"

    snapshot = PosService().stock_snapshot(store=connection.store, skus=[sku])
    payload = {"event": "stock.updated", "item": snapshot[0] if snapshot else {"sku": sku}}
    body = json.dumps(payload).encode()

    request = urllib.request.Request(
        connection.webhook_url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-POS-Signature": keys.sign_payload(connection.webhook_secret, body),
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=WEBHOOK_TIMEOUT) as resp:
            return f"sent:{resp.status}"
    except (urllib.error.URLError, OSError) as exc:
        logger.warning("POS webhook to %s failed: %s", connection.webhook_url, exc)
        # Retry transient failures; give up quietly after max_retries.
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return "failed"


@shared_task(name="pos.push_order_to_cashier", max_retries=3, default_retry_delay=60, bind=True)
def push_order_to_cashier(self, order_id: str) -> str:
    """Push a confirmed store order to the linked cashier's order log. Idempotent
    on the cashier side (external_id), so a retry is safe. Only transient
    (unavailable) failures are retried; an invalid key just fails quietly."""
    from apps.orders.models import Order
    from apps.pos.client import PosAuthError, PosUnavailableError
    from apps.pos.models import PosSupplierConnection
    from apps.pos.services import PosSupplierService

    order = (
        Order.all_objects.filter(id=order_id, is_deleted=False)
        .select_related("store")
        .prefetch_related("items__variant__product")
        .first()
    )
    if order is None:
        return "skipped"
    connection = PosSupplierConnection.all_objects.filter(
        store=order.store, is_connected=True, is_deleted=False
    ).first()
    if connection is None:
        return "skipped"
    try:
        result = PosSupplierService().push_order(connection=connection, order=order)
        return f"pushed:{result.get('id', '')}"
    except PosUnavailableError as exc:
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return "failed"
    except (PosAuthError, Exception) as exc:  # noqa: BLE001 — best-effort, don't retry auth/data errors
        logger.warning("POS order push failed for %s: %s", order_id, exc)
        return "failed"
