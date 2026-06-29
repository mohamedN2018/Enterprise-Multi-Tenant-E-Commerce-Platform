"""Request-scoped tenancy & actor context.

Row-level multi-tenancy is enforced by carrying the *current store* and the
*current user* in :class:`contextvars.ContextVar` instances. ContextVars are
safe under both threaded (WSGI/Gunicorn) and async (ASGI/Channels) execution
and isolate state per request/task — there is no cross-request leakage.

Population happens in :class:`apps.core.middleware.CurrentRequestMiddleware`
(HTTP requests) and may be set explicitly inside Celery tasks / management
commands via :func:`tenant_context`.

Consumers:
    * :class:`apps.core.managers.TenantManager` auto-filters querysets by the
      current store.
    * :class:`apps.core.models.base.BaseModel` stamps ``created_by`` /
      ``updated_by`` from the current user.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any, Iterator, Optional

if TYPE_CHECKING:  # pragma: no cover
    from contextvars import Token

# The values are intentionally typed loosely (Any) so this module never needs
# to import domain models (Store / User), keeping the shared kernel dependency-free.
_current_store: ContextVar[Optional[Any]] = ContextVar("current_store", default=None)
_current_user: ContextVar[Optional[Any]] = ContextVar("current_user", default=None)


# --- Store -----------------------------------------------------------------
def get_current_store() -> Optional[Any]:
    """Return the active tenant (Store) for this request/task, or ``None``."""
    return _current_store.get()


def set_current_store(store: Optional[Any]) -> "Token":
    return _current_store.set(store)


def reset_current_store(token: "Token") -> None:
    _current_store.reset(token)


# --- User ------------------------------------------------------------------
def get_current_user() -> Optional[Any]:
    """Return the authenticated actor for this request/task, or ``None``."""
    return _current_user.get()


def set_current_user(user: Optional[Any]) -> "Token":
    return _current_user.set(user)


def reset_current_user(token: "Token") -> None:
    _current_user.reset(token)


@contextmanager
def tenant_context(
    *, store: Optional[Any] = None, user: Optional[Any] = None
) -> Iterator[None]:
    """Temporarily bind a store/user — for Celery tasks, scripts and tests.

    Example::

        with tenant_context(store=store, user=actor):
            service.do_work()
    """
    store_token = set_current_store(store)
    user_token = set_current_user(user)
    try:
        yield
    finally:
        reset_current_store(store_token)
        reset_current_user(user_token)
