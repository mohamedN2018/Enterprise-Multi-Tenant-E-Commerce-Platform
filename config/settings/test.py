"""Test settings: fast and hermetic."""

from .base import *  # noqa: F403
from .base import SIMPLE_JWT, env

DEBUG = False
ALLOWED_HOSTS = ["*"]

# Deterministic, sufficiently long signing key (avoids short-key warnings).
SIMPLE_JWT["SIGNING_KEY"] = "test-signing-key-that-is-comfortably-over-32-bytes-long"

# Fast password hashing for tests.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# In-memory cache; never touch a real Redis during tests.
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# Run Celery tasks eagerly and synchronously.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# In-memory SQLite by default for fast, hermetic local runs. CI overrides with
# TEST_DATABASE_URL=postgres://... to exercise the production database engine.
DATABASES = {"default": env.db("TEST_DATABASE_URL", default="sqlite://:memory:")}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
