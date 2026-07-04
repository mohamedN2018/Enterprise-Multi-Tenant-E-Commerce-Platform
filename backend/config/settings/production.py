"""Production settings: security-hardened, fail-fast on misconfiguration."""

from .base import *  # noqa: F403
from .base import CACHES, CHANNEL_LAYERS, env

DEBUG = False

# Secrets must be provided explicitly in production.
SECRET_KEY = env("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

# --- HTTPS / cookies / HSTS ---
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_REFERRER_POLICY = "same-origin"

# --- Realtime: Redis-backed channel layer ---
CHANNEL_LAYERS["default"] = {
    "BACKEND": "channels_redis.core.RedisChannelLayer",
    "CONFIG": {"hosts": [env("REDIS_URL", default="redis://redis:6379/0")]},
}

# Cache MUST be a shared store (Redis) in production. DRF throttle counters live
# in the cache — a per-process LocMemCache fallback would multiply every rate
# limit by the worker/pod count and reset on restart, gutting the brute-force /
# credential-stuffing protection on login, registration and password reset.
CACHES["default"] = {
    "BACKEND": "django.core.cache.backends.redis.RedisCache",
    "LOCATION": env("REDIS_URL", default="redis://redis:6379/0"),
}

# --- Error monitoring (optional) ---
SENTRY_DSN = env("DJANGO_SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=env.float("SENTRY_TRACES_RATE", default=0.1),
        send_default_pii=False,
    )
