"""Machine-to-machine auth for the cashier: a per-store API key.

The cashier presents the key as ``X-POS-Key: <key>`` (or ``Authorization: Api-Key
<key>``). We look the row up by its non-secret prefix, then constant-time verify
the hash. On success the request is bound to the connection's store so the
tenant-scoped managers resolve correctly.
"""

from __future__ import annotations

from django.contrib.auth.models import AnonymousUser
from rest_framework import authentication, exceptions, permissions

from apps.core import tenancy
from apps.pos import keys
from apps.pos.models import PosConnection

HEADER = "HTTP_X_POS_KEY"


def _extract_key(request) -> str | None:
    key = request.META.get(HEADER)
    if key:
        return key.strip()
    auth = authentication.get_authorization_header(request).decode("latin1")
    if auth.lower().startswith("api-key "):
        return auth[len("api-key ") :].strip()
    return None


class PosApiKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        key = _extract_key(request)
        if not key:
            return None  # fall through to other authenticators / anonymous
        connection = (
            PosConnection.all_objects.filter(
                api_key_prefix=keys.key_prefix(key), is_active=True, is_deleted=False
            )
            .select_related("store")
            .first()
        )
        if connection is None or not keys.verify_key(key, connection.api_key_hash):
            raise exceptions.AuthenticationFailed("Invalid POS API key.")
        # Bind tenant context so store-scoped managers resolve to this store. The
        # principal is anonymous (a machine, not a human) — the connection travels
        # on request.auth / request.pos_connection, so POS-driven records carry no
        # created_by. Authorisation is enforced by HasPosConnection below.
        tenancy.set_current_store(connection.store)
        request.pos_connection = connection
        return AnonymousUser(), connection

    def authenticate_header(self, request) -> str:
        return "Api-Key"


class HasPosConnection(permissions.BasePermission):
    message = "A valid POS API key is required."

    def has_permission(self, request, view) -> bool:
        return getattr(request, "pos_connection", None) is not None
