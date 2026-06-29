"""Security audit logging service."""

from __future__ import annotations

from apps.accounts.models import SecurityEvent, User
from apps.accounts.repositories import SecurityEventRepository
from apps.core.services import BaseService


class SecurityService(BaseService):
    def __init__(self, repository: SecurityEventRepository | None = None) -> None:
        self.repository = repository or SecurityEventRepository()

    def log(
        self,
        event_type: str,
        *,
        user: User | None = None,
        email: str = "",
        meta: dict | None = None,
        extra: dict | None = None,
    ) -> SecurityEvent:
        meta = meta or {}
        return self.repository.record(
            event_type=event_type,
            user=user,
            email=email,
            ip_address=meta.get("ip"),
            user_agent=meta.get("user_agent", ""),
            metadata=extra or {},
        )
