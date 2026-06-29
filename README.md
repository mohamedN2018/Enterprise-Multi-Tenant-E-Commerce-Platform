# Enterprise Multi-Tenant E-Commerce Platform

A production-grade, **Shopify-style multi-tenant** e-commerce backend: a single
central system hosting many independent storefronts. Built with Django 5, DRF,
Channels, Celery, PostgreSQL, Redis and MinIO.

## Architecture at a glance

- **Topology:** Isolated stores. Each `Store` is a hard tenant boundary — its own
  customers, catalog, carts, checkout and orders. No cross-store shopping.
- **Tenant isolation:** Row-level on a shared schema. Every tenant-owned row
  carries a `store` FK, enforced by a tenant-resolution middleware, scoped
  managers, and DB constraints. Chosen for scale (thousands of tenants).
- **Layered / Clean Architecture:** `models → repositories → services → views`,
  with a reusable **core shared kernel** (base models, managers, repository &
  service bases, exception/response envelope, pagination, permissions, tenancy).
- **Cross-cutting model contract** (`apps.core.models.BaseModel`): UUID primary
  keys, `created_at`/`updated_at`, soft-delete, and audit (`created_by`/`updated_by`,
  auto-stamped from the request actor).

```
config/            Django project (split settings, urls, asgi/wsgi, celery)
apps/
  core/            Shared kernel: base models, managers, repo/service, exceptions,
                   response envelope, pagination, permissions, tenancy, middleware
  accounts/        Custom email-login User (UUID PK)
requirements/      base · development · production
docker/            Dockerfile (python:3.13-slim) · entrypoint
docker-compose.yml web · worker · beat · postgres · redis · minio
```

## Quickstart (Docker — recommended)

```bash
cp .env.example .env          # adjust secrets
docker compose up --build     # starts web, worker, beat, postgres, redis, minio
```

- API base: `http://localhost:8000/api/v1/`
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`
- Health: `http://localhost:8000/health/`
- Admin: `http://localhost:8000/admin/`

Create an admin user: `docker compose exec web python manage.py createsuperuser`

## Local (without Docker)

Requires a running PostgreSQL + Redis (or set `DATABASE_URL` to SQLite for quick
checks). Python 3.13 recommended (3.11+ supported).

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements/development.txt
python manage.py migrate
python manage.py runserver
```

## Testing & quality

```bash
pytest                 # test suite (config/settings/test.py)
ruff check .           # lint
ruff format .          # format
mypy .                 # static typing
```

## Response envelope

Every JSON response shares one shape:

```json
{ "success": true, "message": "OK", "data": { }, "errors": null }
```

Errors set `success: false` with `errors` and an `error_code`; paginated lists
add `meta.pagination`.

## Build status

**Feature 0 — Foundation + Custom User: complete and verified.**
`manage.py check` passes for development/production/test; migrations apply; the
custom User (UUID PK, Argon2, soft-delete) is verified end-to-end.

See the per-feature roadmap in the project notes; Authentication is next.
