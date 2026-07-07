"""Push stock changes out to a linked cashier when stock is committed online.

Fires on the ``stock_committed`` domain signal (an online sale or a stock issue).
Sales the cashier itself reported are skipped — their reference is tagged
``pos-sale:`` — so a POS-driven deduction never echoes back to the same POS.

The webhook is dispatched on transaction commit, in a Celery task, so it never
blocks or rolls back the sale.
"""

from __future__ import annotations

from django.db import transaction
from django.dispatch import receiver

from apps.core.signals import stock_committed
from apps.pos.models import PosConnection


@receiver(stock_committed, dispatch_uid="pos.push_stock_update")
def on_stock_committed(sender, store, variant, warehouse, quantity, reference="", **kwargs) -> None:
    if str(reference or "").startswith("pos-sale:"):
        return  # originated from the cashier; don't echo it back
    connection = PosConnection.all_objects.filter(
        store=store, is_active=True, is_deleted=False
    ).exclude(webhook_url="").first()
    if connection is None:
        return
    from apps.pos.tasks import push_stock_update

    connection_id, sku = str(connection.id), variant.sku
    transaction.on_commit(lambda: push_stock_update.delay(connection_id, sku))
