# Enterprise Multi-Tenant E-Commerce Platform

A production-grade, **Shopify-style multi-tenant** e-commerce platform: a Django/DRF
JWT API hosting many isolated storefronts, plus a React admin console. Built with
Django 5, DRF, Channels, Celery, PostgreSQL and Redis.

## Repository layout

```
backend/            Django/DRF API (the whole server)
  config/           Project: split settings, urls, asgi/wsgi, celery
  apps/             Domain apps (catalog, orders, payments, inventory, …)
  requirements/     base · development · production
  Dockerfile        python:3.13-slim → Gunicorn/Uvicorn
  entrypoint.sh     wait-for-db → migrate → collectstatic → run
frontend/           React admin (Vite + react-bootstrap + ApexCharts)
  src/              App code (api client, contexts, generic resource pages)
  Dockerfile        node build → nginx (serves SPA + reverse-proxies the API)
  nginx.conf        single-origin proxy to the backend
docker-compose.yml      Production / Dokploy stack
docker-compose.dev.yml  Local dev stack (hot-reload)
.env.example            Environment template
```

## Architecture at a glance

- **Topology:** Isolated stores. Each `Store` is a hard tenant boundary — its own
  customers, catalog, carts, checkout and orders.
- **Tenant isolation:** Row-level on a shared schema. Every tenant-owned row carries
  a `store` FK, enforced by tenant-resolution middleware (`X-Store-Id` header),
  scoped managers, and DB constraints.
- **Layered / Clean Architecture:** `models → repositories → services → views`, over a
  reusable core kernel (base models, exceptions, response envelope, pagination,
  permissions, tenancy).
- **Model contract** (`apps.core.models.BaseModel`): UUID PKs, timestamps, soft-delete,
  audit stamps.
- **Single-origin frontend:** the React SPA and the API are served behind one domain —
  nginx serves the SPA and reverse-proxies `/api`, `/django-admin`, `/static`, `/media`, `/ws`
  to the backend (no CORS).

## Quickstart — production stack (Docker)

```bash
cp .env.example .env          # set DJANGO_SECRET_KEY, passwords, your domain
docker compose up --build -d  # db, redis, backend, worker, beat, frontend
docker compose exec backend python manage.py seed_demo   # optional demo data
```

Then open `http://localhost:8080` (the frontend; change with `FRONTEND_PORT`).
Demo login after `seed_demo`: `owner@demo.com` / `Demo12345!`.

Backend routes (proxied through the frontend, or reachable internally):
`/api/v1/` · `/api/docs/` (Swagger) · `/health/` · `/django-admin/` (Django admin;
the React seller console is at `/admin`).

## Local development (hot-reload)

```bash
cp .env.example .env          # for dev you may set DJANGO_SETTINGS_MODULE=config.settings.development
docker compose -f docker-compose.dev.yml up --build
# backend → http://localhost:8000   frontend (Vite) → http://localhost:3000
```

Without Docker: run the backend from `backend/` (`pip install -r requirements/development.txt`,
`python manage.py migrate runserver`) and the frontend from `frontend/` (`npm install && npm run start`).

## Deploy on Dokploy

1. **Create → Compose** in Dokploy, pointing at this repository. It uses
   `docker-compose.yml` (the default).
2. **Environment:** paste the variables from `.env.example`. At minimum set a strong
   `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD` (and the matching `DATABASE_URL`), and add
   your domain to `DJANGO_ALLOWED_HOSTS`. Keep `DJANGO_SECURE_SSL_REDIRECT=False`
   (Dokploy/Traefik terminates TLS and proxies HTTP internally).
3. **Domain:** attach your domain to the **`frontend`** service, container port **80**.
   The frontend nginx proxies API/admin traffic to the backend, so this single domain
   serves the whole app.
4. Deploy. The backend entrypoint waits for Postgres, runs migrations and
   `collectstatic` automatically. Seed demo data (optional) from the Dokploy terminal:
   `python manage.py seed_demo`.

> Split-domain alternative: give the backend its own domain, set
> `VITE_API_URL=https://api.yourdomain` and `CORS_ALLOWED_ORIGINS=https://app.yourdomain`,
> and rebuild the frontend.

## Testing & quality (backend)

```bash
cd backend
pytest apps                 # full suite (config/settings/test.py)
ruff check apps config      # lint
ruff format --check apps config
```

## Response envelope

Every JSON response shares one shape:

```json
{ "success": true, "message": "OK", "data": { }, "errors": null, "meta": { } }
```

Errors set `success: false` with `errors` + an `error_code`; paginated lists put the
array in `data` and pagination info in `meta.pagination`.
