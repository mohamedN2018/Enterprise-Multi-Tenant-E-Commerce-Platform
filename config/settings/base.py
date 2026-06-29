"""
Base settings shared by all environments.

Environment-specific modules (development/production/test) import everything
from here and override only what differs. Configuration is read from the
environment (12-factor) via django-environ.
"""

from datetime import timedelta
from pathlib import Path

import environ

# --- Paths -----------------------------------------------------------------
# base.py -> settings/ -> config/ -> <project root>
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
# Load a .env file at the project root if present (optional in containers).
environ.Env.read_env(BASE_DIR / ".env")

# --- Core ------------------------------------------------------------------
SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-dev-only-key-change-me")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# --- Applications ----------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "corsheaders",
    "drf_spectacular",
    "channels",
    "django_celery_beat",
    "django_celery_results",
]

LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.stores",
    "apps.catalog",
    "apps.inventory",
    "apps.orders",
    "apps.payments",
    "apps.promotions",
    "apps.pricing",
    "apps.finance",
    "apps.rewards",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# --- Middleware ------------------------------------------------------------
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Resolves the current tenant (Store) + actor into a ContextVar and
    # guarantees teardown after the response.
    "apps.core.middleware.CurrentRequestMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Database --------------------------------------------------------------
DATABASES = {
    "default": {
        **env.db(
            "DATABASE_URL",
            default="postgres://marketplace:marketplace@localhost:5432/marketplace",
        ),
        "CONN_MAX_AGE": env.int("DB_CONN_MAX_AGE", default=60),
        "ATOMIC_REQUESTS": False,
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Authentication --------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Argon2 first (OWASP-recommended), PBKDF2 retained for compatibility.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

# --- Internationalization --------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- Static & media --------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Object storage (S3 / MinIO). Enabled via USE_S3; otherwise local filesystem.
USE_S3 = env.bool("USE_S3", default=False)
if USE_S3:
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3.S3Storage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default=None)
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="us-east-1")
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = True
else:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }

# --- Cache -----------------------------------------------------------------
CACHES = {
    "default": env.cache("CACHE_URL", default="locmemcache://"),
}

# --- Email -----------------------------------------------------------------
vars().update(env.email_url("EMAIL_URL", default="consolemail://"))
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@marketplace.local")

# --- Django REST Framework -------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "apps.core.responses.EnvelopeJSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": env("THROTTLE_ANON", default="60/min"),
        "user": env("THROTTLE_USER", default="1000/min"),
        # Sensitive auth endpoints (brute-force / abuse protection).
        "auth_login": env("THROTTLE_AUTH_LOGIN", default="10/min"),
        "auth_register": env("THROTTLE_AUTH_REGISTER", default="5/min"),
        "auth_password_reset": env("THROTTLE_AUTH_PASSWORD_RESET", default="5/min"),
        "auth_email_verification": env("THROTTLE_AUTH_EMAIL_VERIFICATION", default="5/min"),
    },
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    "DEFAULT_VERSION": "v1",
    "ALLOWED_VERSIONS": ["v1"],
}

# --- SimpleJWT -------------------------------------------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("JWT_ACCESS_MINUTES", default=15)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_DAYS", default=7)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": env("JWT_SIGNING_KEY", default=SECRET_KEY),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
}

# --- drf-spectacular (OpenAPI) ---------------------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "Marketplace API",
    "DESCRIPTION": "Enterprise multi-tenant (Shopify-style) e-commerce backend.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]+",
    "COMPONENT_SPLIT_REQUEST": True,
    "SORT_OPERATIONS": False,
}

# --- CORS ------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_CREDENTIALS = True

# --- Channels --------------------------------------------------------------
CHANNEL_LAYERS = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
}

# --- Celery ----------------------------------------------------------------
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/2")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="django-db")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_RESULT_EXTENDED = True

# --- Security headers (hardened further in production.py) -------------------
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# --- Tenancy ---------------------------------------------------------------
# Callable(request) -> Store|None used by CurrentRequestMiddleware to resolve the
# active tenant from request headers / subdomain.
TENANT_RESOLVER = env("TENANT_RESOLVER", default="apps.stores.tenancy.resolve_store")

# --- Authentication flows --------------------------------------------------
# Frontend base URL used to build verification / password-reset links in emails.
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")
FRONTEND_EMAIL_VERIFICATION_PATH = env(
    "FRONTEND_EMAIL_VERIFICATION_PATH", default="/auth/verify-email"
)
FRONTEND_PASSWORD_RESET_PATH = env("FRONTEND_PASSWORD_RESET_PATH", default="/auth/reset-password")

# --- Payments --------------------------------------------------------------
# Allow-list of payment gateway codes exposed by the API (must be registered).
PAYMENT_ENABLED_GATEWAYS = env.list("PAYMENT_ENABLED_GATEWAYS", default=["manual", "store_credit"])
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")

# --- Rewards ---------------------------------------------------------------
REWARDS = {
    # Loyalty points earned per unit of order total (0 = disabled / no-op).
    "LOYALTY_EARN_RATE": env.float("LOYALTY_EARN_RATE", default=0.0),
    # Wallet credit granted per loyalty point on redemption.
    "LOYALTY_REDEEM_RATE": env("LOYALTY_REDEEM_RATE", default="0.01"),
}

AUTH_SETTINGS = {
    # Block login until the email address is verified.
    "REQUIRE_EMAIL_VERIFICATION": env.bool("REQUIRE_EMAIL_VERIFICATION", default=True),
    # One-time token lifetimes.
    "EMAIL_VERIFICATION_TTL_HOURS": env.int("EMAIL_VERIFICATION_TTL_HOURS", default=48),
    "PASSWORD_RESET_TTL_HOURS": env.int("PASSWORD_RESET_TTL_HOURS", default=2),
    # "Remember me" extends the refresh-token lifetime at login time.
    "REMEMBER_ME_REFRESH_DAYS": env.int("REMEMBER_ME_REFRESH_DAYS", default=30),
}

# --- Logging ---------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {process:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"handlers": ["console"], "level": env("DJANGO_LOG_LEVEL", default="INFO")},
    "loggers": {
        "django.db.backends": {"level": "WARNING", "handlers": ["console"], "propagate": False},
    },
}
