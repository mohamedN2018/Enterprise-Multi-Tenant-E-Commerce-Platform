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
# Default (production) command: ASGI server with Uvicorn workers under Gunicorn.
CMD ["gunicorn", "config.asgi:application", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
