"""Development settings: developer ergonomics over hardening."""
from .base import *  # noqa: F401,F403
from .base import REST_FRAMEWORK, env

DEBUG = True
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["*"])

# Expose the browsable API for manual exploration in development.
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
    "apps.core.responses.EnvelopeJSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]

# Relaxed CORS for local frontends.
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=True)

# Email goes to the console unless overridden.
EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
