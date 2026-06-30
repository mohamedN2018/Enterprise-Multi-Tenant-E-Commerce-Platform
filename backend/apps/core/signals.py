"""Cross-cutting domain signals (the shared kernel's observer hooks).

Domain apps *emit* these after a state change; observer apps (notifications,
analytics) *connect* receivers in their ``AppConfig.ready()``. This keeps
producers decoupled from consumers — ``orders`` never imports ``notifications``.

Each signal sends the affected aggregate as a keyword argument (e.g. ``order=``).
Receivers must be defensive about optional related data and should not assume a
request/tenant context beyond what the payload carries.
"""

from __future__ import annotations

import django.dispatch

# kwargs: order (apps.orders.models.Order)
order_placed = django.dispatch.Signal()
order_confirmed = django.dispatch.Signal()
order_cancelled = django.dispatch.Signal()

# Stock left a warehouse for good (a sale commit or a production issue).
# kwargs: store, variant, warehouse, quantity, reference
stock_committed = django.dispatch.Signal()
