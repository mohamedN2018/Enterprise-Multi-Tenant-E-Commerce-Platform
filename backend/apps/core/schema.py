"""OpenAPI schema customizations (drf-spectacular).

The platform is multi-tenant: store-scoped endpoints resolve the active store
from the ``X-Store-Id`` (or ``X-Store-Slug``) request header. That header is not
a view/serializer field, so it is injected into the documented operations here
via a postprocessing hook — giving a generated frontend SDK the tenant header on
every store-scoped call.
"""

from __future__ import annotations

_TENANT_HEADERS = [
    {
        "name": "X-Store-Id",
        "in": "header",
        "required": False,
        "description": "Active store (tenant) UUID. Required by store-scoped "
        "endpoints; alternatively send X-Store-Slug.",
        "schema": {"type": "string", "format": "uuid"},
    },
    {
        "name": "X-Store-Slug",
        "in": "header",
        "required": False,
        "description": "Active store (tenant) slug — an alternative to X-Store-Id.",
        "schema": {"type": "string"},
    },
]

# Operations that never need a tenant context.
_EXEMPT_PREFIXES = ("/api/v1/auth/", "/api/schema", "/health")
_METHODS = {"get", "post", "put", "patch", "delete"}


def add_tenant_header(result, generator, request, public):
    """Add the X-Store-Id / X-Store-Slug headers to every store-scoped operation."""
    for path, item in result.get("paths", {}).items():
        if any(path.startswith(prefix) for prefix in _EXEMPT_PREFIXES):
            continue
        for method, operation in item.items():
            if method not in _METHODS or not isinstance(operation, dict):
                continue
            params = operation.setdefault("parameters", [])
            existing = {p.get("name") for p in params if isinstance(p, dict)}
            for header in _TENANT_HEADERS:
                if header["name"] not in existing:
                    params.append(header)
    return result
