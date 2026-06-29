"""Device / session management service."""

from __future__ import annotations

from django.db.models import QuerySet

from apps.accounts.models import SecurityEventType, User, UserDevice
from apps.accounts.repositories import UserDeviceRepository
from apps.accounts.services import jwt
from apps.accounts.services.security import SecurityService
from apps.core.exceptions import NotFoundError
from apps.core.services import BaseService


class DeviceService(BaseService):
    def __init__(
        self,
        *,
        device_repo: UserDeviceRepository | None = None,
        security: SecurityService | None = None,
    ) -> None:
        self.device_repo = device_repo or UserDeviceRepository()
        self.security = security or SecurityService()

    def list_active(self, user: User) -> QuerySet[UserDevice]:
        return self.device_repo.active_for_user(user)

    def revoke(self, *, user: User, device_id, meta: dict) -> None:
        device = self.device_repo.get_or_none(id=device_id, user=user, is_active=True)
        if device is None:
            raise NotFoundError("Device not found.")
        jwt.blacklist_jti(device.jti)
        self.device_repo.deactivate(device)
        self.security.log(
            SecurityEventType.DEVICE_REVOKED,
            user=user,
            meta=meta,
            extra={"device_id": str(device_id)},
        )

    def revoke_all(self, *, user: User, meta: dict) -> int:
        count = 0
        for device in self.device_repo.active_for_user(user):
            jwt.blacklist_jti(device.jti)
            self.device_repo.deactivate(device)
            count += 1
        self.security.log(
            SecurityEventType.DEVICE_REVOKED,
            user=user,
            meta=meta,
            extra={"revoked_all": True, "count": count},
        )
        return count
