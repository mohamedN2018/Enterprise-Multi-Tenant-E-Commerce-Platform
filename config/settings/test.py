"""Test settings: fast and hermetic."""
from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False
ALLOWED_HOSTS = ["*"]

# Fast password hashing for tests.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# In-memory cache; never touch a real Redis during tests.
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# Run Celery tasks eagerly and synchronously.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Default to a local Postgres test DB; override with DATABASE_URL in CI.
DATABASES = {
    "default": env.db(
        "TEST_DATABASE_URL",
        default="postgres://marketplace:marketplace@localhost:5432/marketplace_test",
    )
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
