# syntax=docker/dockerfile:1
# ===========================================================================
# Multi-stage build for the marketplace backend (Django / DRF).
# Build context: ./backend   ·   Production parity: Python 3.13 (Debian slim).
# ===========================================================================

FROM python:3.13-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

# System dependencies: psycopg (libpq), Pillow (libjpeg/zlib), ffmpeg (media), curl (healthcheck).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libjpeg-dev \
        zlib1g-dev \
        ffmpeg \
        curl \
    && rm -rf /var/lib/apt/lists/*

# --- Dependencies layer (cached unless requirements change) ---
FROM base AS deps
ARG REQUIREMENTS=requirements/production.txt
COPY requirements/ requirements/
RUN pip install -r ${REQUIREMENTS}

# --- Final image ---
FROM deps AS final
COPY . .

# Non-root runtime user; writable static/media dirs.
RUN addgroup --system app \
    && adduser --system --ingroup app --home /app app \
    && mkdir -p /app/staticfiles /app/media \
    && chown -R app:app /app
USER app

EXPOSE 8000

ENTRYPOINT ["sh", "/app/entrypoint.sh"]
# Default (production) command: the WSGI app under Gunicorn with threaded sync
# workers. The API is fully synchronous (DRF views + ORM); serving it via the
# ASGI/Uvicorn worker ran DB access in an async context and raised
# SynchronousOnlyOperation under concurrency (login/theme → 504/502). No
# WebSocket consumers are wired yet (see config/asgi.py), so WSGI loses nothing;
# switch back to config.asgi with an async-safe stack when realtime lands.
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--threads", "4", \
     "--worker-class", "gthread", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
