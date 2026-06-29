"""Service layer base.

Services hold business logic / use-cases. They orchestrate repositories,
enforce invariants, and own transactional boundaries — keeping views thin and
models persistence-focused (Clean Architecture / SOLID).
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import TypeVar

from django.db import transaction

T = TypeVar("T")


def atomic(func: Callable[..., T]) -> Callable[..., T]:
    """Wrap a service method in a database transaction."""

    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        with transaction.atomic():
            return func(*args, **kwargs)

    return wrapper


class BaseService:
    """Marker/base class for application services.

    Subclasses inject the repositories they need and expose intention-revealing
    methods. Wrap mutating operations with :func:`atomic` (or
    ``transaction.atomic``) and raise ``apps.core.exceptions`` domain errors.
    """
