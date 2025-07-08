import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
from datetime import timedelta


# ─── Load environment variables ────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

# ─── Security & Debug ───────────────────────────────────────
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-CHANGE_ME')
DEBUG = os.getenv('DEBUG', '1') == '1'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')

# ─── Installed Apps ─────────────────────────────────────────
INSTALLED_APPS = [
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third‑party
    'rest_framework',
    'corsheaders',
    'django_celery_beat',

    # Your apps
    'accounts',
    'tracking',
    'referrals',
    'agents',
    'core',  # for API versioning and future expansion
    'rest_framework_simplejwt.token_blacklist',
    'bookings.apps.BookingsConfig',
]


CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True


# ─── Middleware ────────────────────────────────────────────
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',            # must come first
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# Optional: Cache static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ─── CORS (dev only) ───────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True
# in production, replace with:
# CORS_ALLOWED_ORIGINS = ['https://app.cargo-ghana.com']

# ─── URL Configuration ─────────────────────────────────────
ROOT_URLCONF = 'cargo_ghana_engine.urls'

# ─── Templates ─────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # add BASE_DIR/'templates' if you use templates
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

# ─── WSGI ───────────────────────────────────────────────────
WSGI_APPLICATION = 'cargo_ghana_engine.wsgi.application'

# ─── Database ──────────────────────────────────────────────
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR/"db.sqlite3"}'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ─── Static & Media ───────────────────────────────────────
# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']


MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'



# ─── Custom User ───────────────────────────────────────────
AUTH_USER_MODEL = 'accounts.User'

# ─── Django REST Framework ─────────────────────────────────
REST_FRAMEWORK = {
    # — Authentication backends only —
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        # (or JWTAuthentication if you’re using Simple JWT)
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],

    # — Default permissions —
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],

    # — Throttle classes (separate!) —
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
    },
}


# Compression
django_compressor = True
COMPRESS_ENABLED = True
COMPRESS_ROOT = STATIC_ROOT
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
]


# ─── Celery Configuration ──────────────────────────────────
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = CELERY_BROKER_URL

# ─── Internationalization ──────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True



# ─── Default Primary Key Field ────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    # ...
}