"""Domain-signal receivers: deplete batches FEFO when stock leaves a warehouse.

Connected in :class:`apps.procurement.apps.ProcurementConfig.ready`. Runs inside
the committing transaction (a sale or a production issue) so the batch ledger
moves with the stock. A no-op for variants that have no batches.
"""

from __future__ import annotations

from django.dispatch import receiver

from apps.core.signals import stock_committed
from apps.procurement.services import ProcurementService


@receiver(stock_committed, dispatch_uid="procurement.fefo_consume")
def on_stock_committed(sender, store, variant, warehouse, quantity, **kwargs) -> None:
    ProcurementService().consume_batches_fefo(
        store=store, variant=variant, warehouse=warehouse, quantity=quantity
    )
