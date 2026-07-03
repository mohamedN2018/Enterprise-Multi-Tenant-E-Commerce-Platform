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
cp .env.example .env               # set DJANGO_SECRET_KEY, passwords, your domain
docker network create dokploy-network 2>/dev/null || true   # the shared network (Dokploy already has it)
docker compose up --build -d       # qshop-db, qshop-redis, qshop-backend, qshop-worker, qshop-beat, qshop-frontend
docker compose exec qshop-backend python manage.py seed_demo   # optional demo data
```

Then open `http://localhost:8080` (the frontend; change with `FRONTEND_PORT`).
Demo login after `seed_demo`: `owner@demo.com` / `Demo12345!`.
On Dokploy the `dokploy-network` already exists, so skip the `network create` step.

Backend routes (proxied through the frontend, or reachable internally):
`/api/v1/` · `/api/docs/` (Swagger) · `/health/` · `/django-admin/` (Django admin;
the React seller console is at `/admin`).

## Local development

**Database:** development settings use **SQLite** by default (a `backend/db.sqlite3`
file — no DB server to run), while production uses **PostgreSQL** via `DATABASE_URL`.

Simplest local setup (SQLite, no Docker, no Redis — Celery runs inline):

```bash
cd backend
cp .env.example .env           # keep DATABASE_URL commented out → SQLite
pip install -r requirements/development.txt
python manage.py migrate
python manage.py seed_demo     # demo data (works with DEBUG=True; no --force needed)
python manage.py runserver     # http://localhost:8000  (settings default to development)
# in another shell:
cd frontend && npm install && npm run start   # Vite → http://localhost:3000
```

Prefer Postgres locally? Either set `DATABASE_URL=postgres://…` in `backend/.env`, or
run the full containerised dev stack (hot-reload, bundled Postgres/Redis):

```bash
docker compose -f docker-compose.dev.yml up --build
```

## Deploy on Dokploy

1. **Create → Compose** in Dokploy, pointing at this repository. **Set the Compose
   Path to `./docker-compose.yml`** — NOT `docker-compose.dev.yml` (that one is
   local-only: it publishes host ports 5432/6379/8000/3000 and runs dev settings).
2. **Environment:** paste the variables from `.env.example` (or your filled `.env`).
   At minimum set a strong `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD` (and the matching
   `DATABASE_URL`), and add your domain to `DJANGO_ALLOWED_HOSTS` **and**
   `CSRF_TRUSTED_ORIGINS`. Keep `DJANGO_SECURE_SSL_REDIRECT=False` (Dokploy/Traefik
   terminates TLS and proxies HTTP internally).
3. **Domain:** attach your domain to the **`qshop-frontend`** service, container
   port **80**. The frontend nginx proxies API/admin traffic to the backend, so this
   single domain serves the whole app.
4. Deploy. The backend entrypoint waits for Postgres, runs migrations and
   `collectstatic` automatically. Seed demo data (optional) from the Dokploy terminal:
   `python manage.py seed_demo`.

> **No new Docker network is created.** Every service joins Dokploy's existing
> `dokploy-network` (set `DOKPLOY_NETWORK` if yours differs), and service names are
> uniquely prefixed `qshop-*` so they never clash with other apps on that network.
> This is what sidesteps the `all predefined address pools have been fully subnetted`
> error without touching the host. Only `qshop-frontend` publishes a host port
> (`FRONTEND_PORT`, default 8080) — pick an app-unique value, or drop it entirely and
> route through the Dokploy domain.

> Split-domain alternative: give the backend its own domain, set
> `VITE_API_URL=https://api.yourdomain` and `CORS_ALLOWED_ORIGINS=https://app.yourdomain`,
> and rebuild the frontend.

### Troubleshooting

**Deploy fails with `all predefined address pools have been fully subnetted`.**
This is a **Docker host** condition, not a problem with this repo: the daemon has
run out of network subnets to hand out. Every Compose deploy creates a bridge
network, and repeated/failed deploys leave orphaned ones behind until the default
address pool is exhausted. Fix it on the Dokploy **server** (SSH in):

```bash
# Immediate fix — remove unused networks (frees the pool):
docker network prune -f
docker system prune -f          # optional: also clears dangling images/containers

# Then redeploy from the Dokploy UI.
```

If it keeps recurring (a busy host with many apps), enlarge the pool once in
`/etc/docker/daemon.json` and restart Docker:

```json
{
  "default-address-pools": [
    { "base": "172.17.0.0/16", "size": 24 },
    { "base": "172.20.0.0/14", "size": 24 }
  ]
}
```
```bash
sudo systemctl restart docker   # pick ranges that don't overlap your LAN
```

**Django admin (`/django-admin/`) login returns 403 / CSRF failed.** Add your
HTTPS domain to `CSRF_TRUSTED_ORIGINS` (scheme included), e.g.
`CSRF_TRUSTED_ORIGINS=https://shop.example.com`. The storefront/API use JWT and are
unaffected; this only matters for the Django admin behind Dokploy's TLS proxy.

**`DisallowedHost` errors.** Add the domain to `DJANGO_ALLOWED_HOSTS`
(comma-separated, no scheme), keeping `backend` in the list for internal proxying.

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
