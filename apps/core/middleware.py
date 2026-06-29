"""Request-scoped context middleware.

Binds the current actor and tenant (Store) into ContextVars for the lifetime
of the request and guarantees teardown in ``finally`` so state never leaks to
the next request served by the same worker.

The tenant resolver is pluggable via ``settings.TENANT_RESOLVER`` (a dotted path
to ``callable(request) -> Store | None``). It is intentionally unset until the
stores app exists; until then the resolver is a no-op and ``current_store`` is
``None`` (single-tenant/platform context).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from importlib import import_module

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from apps.core import tenancy

logger = logging.getLogger(__name__)


def _load_resolver() -> Callable[[HttpRequest], object] | None:
    path = getattr(settings, "TENANT_RESOLVER", None)
    if not path:
        return None
    module_path, attr = path.rsplit(".", 1)
    return getattr(import_module(module_path), attr)


class CurrentRequestMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        self._resolver = _load_resolver()

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # request.user is a lazy object set by AuthenticationMiddleware (session/admin).
        # JWT-authenticated DRF requests refresh this via BaseAPIViewMixin.initial().
        user_token = tenancy.set_current_user(getattr(request, "user", None))

        store = None
        if self._resolver is not None:
            try:
                store = self._resolver(request)
            except Exception:
                logger.exception("Tenant resolution failed for %s", request.path)
                store = None
        store_token = tenancy.set_current_store(store)

        # Expose on the request object too, for view/permission convenience.
        request.tenant = store  # type: ignore[attr-defined]

        try:
            return self.get_response(request)
        finally:
            tenancy.reset_current_store(store_token)
            tenancy.reset_current_user(user_token)
