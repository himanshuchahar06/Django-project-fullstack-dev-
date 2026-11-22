
"""
Django settings for bookmyseat project.
"""

from pathlib import Path
import os
import shutil
import dj_database_url


# --------------------------------------------------
# BASE DIRECTORY
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent


# --------------------------------------------------
# SECURITY
# --------------------------------------------------

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-change-this-for-local-development"
)

DEBUG = os.environ.get(
    "DEBUG",
    "True"
).lower() == "true"

ALLOWED_HOSTS = [
    "*",
    "localhost",
    "127.0.0.1",
    ".vercel.app",
]

CSRF_TRUSTED_ORIGINS = [
    "https://*.vercel.app",
    "https://*.now.sh",
    "https://django-project-fullstack-dev.vercel.app",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)


# --------------------------------------------------
# APPLICATIONS
# --------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "users",
    "movies",
]


# --------------------------------------------------
# MIDDLEWARE
# --------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
]

try:
    import whitenoise
    MIDDLEWARE.append("whitenoise.middleware.WhiteNoiseMiddleware")
except ImportError:
    pass

MIDDLEWARE += [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# --------------------------------------------------
# USER / AUTHENTICATION
# --------------------------------------------------

AUTH_USER_MODEL = "auth.User"

LOGIN_URL = "/login/"


# --------------------------------------------------
# EMAIL
# --------------------------------------------------

EMAIL_BACKEND = (
    "django.core.mail.backends.console.EmailBackend"
)


# --------------------------------------------------
# MEDIA
# --------------------------------------------------

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# --------------------------------------------------
# URL CONFIGURATION
# --------------------------------------------------

ROOT_URLCONF = "bookmyseat.urls"


# --------------------------------------------------
# TEMPLATES
# --------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",

        "DIRS": [
            BASE_DIR / "templates",
        ],

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


# --------------------------------------------------
# WSGI
# --------------------------------------------------

WSGI_APPLICATION = "bookmyseat.wsgi.application"


# --------------------------------------------------
# DATABASE CONFIGURATION
# --------------------------------------------------

DATABASE_URL = (
    os.environ.get("DATABASE_URL")
    or os.environ.get("POSTGRES_URL")
)

def is_postgres_reachable(url):
    if not url:
        return False
    # If it is the known expired Render database, skip it to prevent SSL connection crashes
    if "dpg-da5ltqijobas73f5fla0-a" in url:
        return False
    try:
        import psycopg2
        cfg = dj_database_url.parse(url)
        conn = psycopg2.connect(
            dbname=cfg.get('NAME'),
            user=cfg.get('USER'),
            password=cfg.get('PASSWORD'),
            host=cfg.get('HOST'),
            port=cfg.get('PORT') or 5432,
            connect_timeout=2
        )
        conn.close()
        return True
    except Exception:
        return False

if DATABASE_URL and is_postgres_reachable(DATABASE_URL):
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=0,
            ssl_require=True,
        )
    }
else:
    if os.environ.get("VERCEL"):
        tmp_db = "/tmp/db.sqlite3"
        bundled_db = str(BASE_DIR / "db.sqlite3")
        if not os.path.exists(tmp_db) and os.path.exists(bundled_db):
            try:
                shutil.copy2(bundled_db, tmp_db)
            except Exception:
                pass
        sqlite_name = tmp_db if os.path.exists(tmp_db) else bundled_db
    else:
        sqlite_name = BASE_DIR / "db.sqlite3"

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": sqlite_name,
        }
    }


# --------------------------------------------------
# PASSWORD VALIDATION
# --------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# --------------------------------------------------
# INTERNATIONALIZATION
# --------------------------------------------------

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# --------------------------------------------------
# STATIC FILES
# --------------------------------------------------

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

try:
    import whitenoise
    STATICFILES_STORAGE = (
        "whitenoise.storage.CompressedStaticFilesStorage"
    )
except ImportError:
    pass


# --------------------------------------------------
# DEFAULT PRIMARY KEY
# --------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --------------------------------------------------
# CELERY
# --------------------------------------------------

CELERY_BROKER_URL = os.environ.get(
    "CELERY_BROKER_URL",
    "redis://localhost:6379/0"
)

CELERY_RESULT_BACKEND = os.environ.get(
    "CELERY_RESULT_BACKEND",
    "redis://localhost:6379/0"
)

CELERY_ACCEPT_CONTENT = ["json"]

CELERY_TASK_SERIALIZER = "json"

CELERY_RESULT_SERIALIZER = "json"

CELERY_TIMEZONE = TIME_ZONE
