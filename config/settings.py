"""
Django settings for the Mbuzi Munch website.

Values that differ between development and production are read from
environment variables (see README.md and .env.example).
"""

import mimetypes
import os
from pathlib import Path

# so the dev server sends the web-app manifest with the right type
mimetypes.add_type("application/manifest+json", ".webmanifest")

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


# Running on Vercel? VERCEL=1 isn't always present inside the serverless function,
# so also look at the other variables Vercel / AWS Lambda set at runtime.
ON_VERCEL = any(
    os.environ.get(name)
    for name in ("VERCEL", "VERCEL_ENV", "VERCEL_URL", "AWS_LAMBDA_FUNCTION_NAME", "LAMBDA_TASK_ROOT")
)

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-only-change-me-in-production",
)
DEBUG = env_bool("DJANGO_DEBUG", not ON_VERCEL)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")
if ON_VERCEL:
    vercel_hosts = ["munchmbuzi.vercel.app", ".vercel.app"] + [
        os.environ[name] for name in ("VERCEL_URL", "VERCEL_BRANCH_URL", "VERCEL_PROJECT_PRODUCTION_URL")
        if os.environ.get(name)
    ]
    ALLOWED_HOSTS += vercel_hosts
    CSRF_TRUSTED_ORIGINS += ["https://munchmbuzi.vercel.app", "https://*.vercel.app"] + [
        f"https://{h}" for h in vercel_hosts if not h.startswith(".") and h != "munchmbuzi.vercel.app"
    ]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.site",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Local development uses SQLite. In production (Vercel) set DATABASE_URL to a
# Postgres database (e.g. Vercel Postgres / Neon): Vercel's file system is
# read-only, so SQLite could not save bookings or job applications there.
if os.environ.get("DATABASE_URL"):
    import dj_database_url

    DATABASES = {"default": dj_database_url.config(conn_max_age=0, conn_health_checks=True)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
    if ON_VERCEL:
        # No Postgres connected: run on a temporary SQLite file in /tmp (the only
        # writable place) so the site still works. config/wsgi.py creates the tables
        # and loads the content on start-up. Bookings made in this mode are LOST
        # whenever Vercel recycles the server, so connect Postgres for real use.
        import sys
        import tempfile

        DATABASES["default"]["NAME"] = os.path.join(tempfile.gettempdir(), "mbuzimunch.sqlite3")
        print(
            "WARNING: DATABASE_URL is not set, using a temporary database. Bookings and "
            "job applications will NOT be kept. Add a Postgres database in Vercel "
            "(Project > Storage) and redeploy.",
            file=sys.stderr,
        )

# Send errors (with full tracebacks) to stdout/stderr so they appear in Vercel's logs.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
# collectstatic writes here; on Vercel the build serves staticfiles_build/ from its CDN.
STATIC_ROOT = BASE_DIR / "staticfiles_build" / "static"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # Plain storage (no hashed manifest) so server functions don't need the build output;
    # CSS/JS cache-busting is handled by the ?v= tag in base.html.
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# CV uploads on the careers form
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Email: bookings and job applications notify the branch / HR inbox.
# In development emails are printed to the console.
EMAIL_BACKEND = os.environ.get(
    "DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "Mbuzi Munch <no-reply@mbuzimunch.com>")
CAREERS_EMAIL = os.environ.get("CAREERS_EMAIL", "galleria@mbuzimunch.com")

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_CONTENT_TYPE_NOSNIFF = True
