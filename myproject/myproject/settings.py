from pathlib import Path
import os

from django.core.exceptions import ImproperlyConfigured


# =========================================================
# BASE DIRECTORY
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# =========================================================
# ENVIRONMENT VARIABLES
# Loads .env from the directory containing manage.py.
# Existing operating-system environment variables take priority.
# =========================================================

def load_env_file(env_path):
    if not env_path.is_file():
        return

    for raw_line in env_path.read_text(
        encoding="utf-8-sig"
    ).splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            continue

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in ("'", '"')
        ):
            value = value[1:-1]

        os.environ.setdefault(key, value)


load_env_file(BASE_DIR / ".env")


def env_bool(name, default=False):
    value = os.getenv(name)

    if value is None:
        return default

    value = value.strip().lower()

    if value in ("1", "true", "yes", "on"):
        return True

    if value in ("0", "false", "no", "off"):
        return False

    raise ImproperlyConfigured(
        f"{name} must be a valid boolean value."
    )


def env_list(name, default=""):
    return [
        item.strip()
        for item in os.getenv(name, default).split(",")
        if item.strip()
    ]


# =========================================================
# SECURITY
# =========================================================

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "").strip()

if not SECRET_KEY:
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY is missing. "
        "Set it in the .env file or server environment."
    )

# False by default: detailed Django error pages stay disabled.
DEBUG = env_bool("DJANGO_DEBUG", False)

ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    "localhost,127.0.0.1",
)

CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "http://localhost:8000,http://127.0.0.1:8000",
)

SECURE_SSL_REDIRECT = env_bool(
    "DJANGO_SECURE_SSL_REDIRECT",
    not DEBUG,
)

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

SECURE_COOKIES = env_bool(
    "DJANGO_SECURE_COOKIES",
    not DEBUG,
)

SESSION_COOKIE_SECURE = SECURE_COOKIES
CSRF_COOKIE_SECURE = SECURE_COOKIES

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

try:
    SECURE_HSTS_SECONDS = int(
        os.getenv("DJANGO_SECURE_HSTS_SECONDS", "0")
    )
except ValueError as exc:
    raise ImproperlyConfigured(
        "DJANGO_SECURE_HSTS_SECONDS must be an integer."
    ) from exc

if SECURE_HSTS_SECONDS < 0:
    raise ImproperlyConfigured(
        "DJANGO_SECURE_HSTS_SECONDS cannot be negative."
    )

SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS",
    False,
)

SECURE_HSTS_PRELOAD = env_bool(
    "DJANGO_SECURE_HSTS_PRELOAD",
    False,
)


# =========================================================
# APPLICATIONS
# =========================================================

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Core
    "core.apps.CoreConfig",
    "users.apps.UsersConfig",
    "utils.apps.UtilsConfig",
    "communications.apps.CommunicationsConfig",
    "maintenance.apps.MaintenanceConfig",
    "jalali_date",

    # Business
    "inventory.apps.InventoryConfig",
    "daily_activity.apps.DailyActivityConfig",
    "union_rates.apps.UnionRatesConfig",

    # CRM
    "crm.apps.CRMConfig",

    # Requests
    "requests.apps.RequestsConfig",

    # Audit & Reports
    "audit.apps.AuditConfig",
    "reports.apps.ReportsConfig",
]


# =========================================================
# MIDDLEWARE
# =========================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# =========================================================
# URLS AND WSGI
# =========================================================

ROOT_URLCONF = "myproject.urls"

WSGI_APPLICATION = "myproject.wsgi.application"


# =========================================================
# TEMPLATES
# =========================================================

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


# =========================================================
# DATABASE
# Preserve the existing SQLite database.
# =========================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# =========================================================
# PASSWORD VALIDATION
# =========================================================

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


# =========================================================
# LANGUAGE AND TIME
# =========================================================

LANGUAGE_CODE = "fa-ir"

TIME_ZONE = "Asia/Tehran"

USE_I18N = True
USE_TZ = True


# =========================================================
# STATIC FILES
# =========================================================

STATIC_URL = "/static/"

STATICFILES_DIRS = (
    [BASE_DIR / "static"]
    if (BASE_DIR / "static").is_dir()
    else []
)

STATIC_ROOT = BASE_DIR / "staticfiles"


# =========================================================
# MEDIA FILES
# =========================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"


# =========================================================
# DEFAULT PRIMARY KEY
# =========================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# =========================================================
# JALALI DATE
# =========================================================

JALALI_DATE_DEFAULTS = {
    "LIST_DISPLAY_AUTO_CONVERT": True,
    "Strftime": {
        "date": "%Y/%m/%d",
        "datetime": "%Y/%m/%d - %H:%M:%S",
    },
}


# =========================================================
# SMS CONFIGURATION
# =========================================================

SMS_PROVIDER = os.getenv("SMS_PROVIDER", "console")

KAVENEGAR_API_KEY = os.getenv("KAVENEGAR_API_KEY", "")

KAVENEGAR_SENDER = os.getenv("KAVENEGAR_SENDER", "")

try:
    MAINTENANCE_MAX_AUTOMATIC_SMS_PER_DAY = int(
        os.getenv("MAINTENANCE_MAX_AUTOMATIC_SMS_PER_DAY", "1")
    )
except ValueError as exc:
    raise ImproperlyConfigured(
        "MAINTENANCE_MAX_AUTOMATIC_SMS_PER_DAY must be an integer."
    ) from exc

if MAINTENANCE_MAX_AUTOMATIC_SMS_PER_DAY < 0:
    raise ImproperlyConfigured(
        "MAINTENANCE_MAX_AUTOMATIC_SMS_PER_DAY cannot be negative."
    )