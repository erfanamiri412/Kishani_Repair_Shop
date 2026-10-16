from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent


# Security

SECRET_KEY = 'django-insecure-i$%ukd31@t62iohb649hn*6n#$*sfyk7r)hvzik72nqxfkhzcz'

DEBUG = True

ALLOWED_HOSTS = []



# Applications

INSTALLED_APPS = [

    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Core
    'core.apps.CoreConfig',
    'users.apps.UsersConfig',
    'utils.apps.UtilsConfig',
    'communications.apps.CommunicationsConfig',
    'maintenance.apps.MaintenanceConfig',
    'jalali_date',

    # Business
    'inventory.apps.InventoryConfig',
    'daily_activity.apps.DailyActivityConfig',
    'union_rates.apps.UnionRatesConfig',

    # CRM
    'crm.apps.CRMConfig',

    # Requests
    'requests.apps.RequestsConfig',

    # Audit & Reports
    'audit.apps.AuditConfig',
    'reports.apps.ReportsConfig',
    
]



# Middleware

MIDDLEWARE = [

    'django.middleware.security.SecurityMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',

    'django.middleware.common.CommonMiddleware',

    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',

    'django.middleware.clickjacking.XFrameOptionsMiddleware',

]



ROOT_URLCONF = 'myproject.urls'



# Templates

TEMPLATES = [

    {

        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [

            BASE_DIR / 'templates'

        ],

        'APP_DIRS': True,


        'OPTIONS': {

            'context_processors': [

                'django.template.context_processors.debug',

                'django.template.context_processors.request',

                'django.contrib.auth.context_processors.auth',

                'django.contrib.messages.context_processors.messages',

            ],

        },

    },

]



WSGI_APPLICATION = 'myproject.wsgi.application'



# Database

DATABASES = {

    'default': {

        'ENGINE': 'django.db.backends.sqlite3',

        'NAME': BASE_DIR / 'db.sqlite3',

    }

}



# Password validation

AUTH_PASSWORD_VALIDATORS = [

    {
        'NAME':
        'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },

    {
        'NAME':
        'django.contrib.auth.password_validation.MinimumLengthValidator',
    },

    {
        'NAME':
        'django.contrib.auth.password_validation.CommonPasswordValidator',
    },

    {
        'NAME':
        'django.contrib.auth.password_validation.NumericPasswordValidator',
    },

]



# Language

LANGUAGE_CODE = 'fa-ir'

TIME_ZONE = 'Asia/Tehran'

USE_I18N = True

USE_TZ = True



# ==========================
# STATIC FILES
# ==========================


STATIC_URL = '/static/'


# محل اصلی فایل‌های استاتیک

STATICFILES_DIRS = [

    BASE_DIR / 'static'

]


# برای collectstatic در آینده

STATIC_ROOT = BASE_DIR / 'staticfiles'



# Media

MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'



DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

JALALI_DATE_DEFAULTS = {
    "LIST_DISPLAY_AUTO_CONVERT": True,

    "Strftime": {
        "date": "%Y/%m/%d",
        "datetime": "%Y/%m/%d - %H:%M:%S",
    },
}

SMS_PROVIDER = os.getenv("SMS_PROVIDER", "console")
KAVENEGAR_API_KEY = os.getenv("KAVENEGAR_API_KEY", "")
KAVENEGAR_SENDER = os.getenv("KAVENEGAR_SENDER", "")
MAINTENANCE_MAX_AUTOMATIC_SMS_PER_DAY = int(os.getenv("MAINTENANCE_MAX_AUTOMATIC_SMS_PER_DAY", "1"))