"""Development settings: developer ergonomics over hardening."""

from .base import *  # noqa: F403
from .base import BASE_DIR, REST_FRAMEWORK, env

DEBUG = True
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["*"])

# --- Database: SQLite by default locally (no Postgres server needed) ---------
# Production uses Postgres via DATABASE_URL. Locally, if DATABASE_URL is unset we
# fall back to a SQLite file; set DATABASE_URL to use Postgres locally instead.
if not env("DATABASE_URL", default=""):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
            "ATOMIC_REQUESTS": False,
        }
    }

# Run Celery tasks inline so no broker/worker (Redis) is required locally.
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=True)
CELERY_TASK_EAGER_PROPAGATES = True

# Expose the browsable API for manual exploration in development.
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
    "apps.core.responses.EnvelopeJSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]

# Relaxed CORS for local frontends.
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=True)

# Email goes to the console unless overridden.
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
