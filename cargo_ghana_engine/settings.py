import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
from datetime import timedelta
from celery.schedules import crontab
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# ─── Load environment variables ────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

# ─── Security & Debug ───────────────────────────────────────
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-CHANGE_ME')
DEBUG = os.getenv('DEBUG', '1') == '1'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')

# ─── Installed Apps ─────────────────────────────────────────
INSTALLED_APPS = [  
    'jazzmin',
    'import_export',  # Add this line
    'django.contrib.admin',  # Keep this
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
    'core',
    'rest_framework_simplejwt.token_blacklist',
    'bookings.apps.BookingsConfig',
    'notification_templates',
]

# Add Jazzmin settings after INSTALLED_APPS
JAZZMIN_SETTINGS = {
    # title of the window (Will default to current_admin_site.site_title if absent or None)
    "site_title": "CargoGhana Admin",
    "site_header": "CargoGhana",
    "site_brand": "CargoGhana Admin",
    "welcome_sign": "Welcome to CargoGhana Logistics Platform",
    "copyright": "CargoGhana Ltd",
    
    # Top Menu Items
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Support", "url": "https://cargoghana.com/support", "new_window": True},
    ],
    
    # Custom icons for side menu apps/models
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "bookings.booking": "fas fa-box",
        "bookings.containerbatch": "fas fa-shipping-fast",
        "bookings.containercapacity": "fas fa-warehouse",
        "bookings.notificationlog": "fas fa-bell",
        "agents.agentapplication": "fas fa-user-tie",
        "referrals.referral": "fas fa-share-alt",
        "tracking": "fas fa-map-marker-alt",
        "accounts.user": "fas fa-user-circle",
        "notification_templates": "fas fa-envelope",
    },
    
    # Custom admin interface settings
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    
    # UI Customizer
    "custom_css": None,
    "custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": True,
    
    # Related Modal
    "related_modal_active": True,
    
    # Custom menu ordering and grouping
    "order_with_respect_to": [
        "auth",
        "bookings",
        "agents",
        "referrals",
        "tracking",
        "accounts",
        "notification_templates",
    ],
    
    # Group apps in custom menus
    "custom_links": {
        "bookings": [{
            "name": "Container Statistics", 
            "url": "admin:bookings_containerbatch_changelist", 
            "icon": "fas fa-chart-bar"
        }],
    },
}

# Custom admin title
JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-success",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": False,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}


CELERY_BEAT_SCHEDULE = {
    'milestone-check-every-hour': {
        'task': 'bookings.tasks.check_milestones_and_notify',
        'schedule': crontab(minute=0),
    },
    'dispatch-ready-check-every-hour': {
        'task': 'bookings.tasks.notify_dispatch_ready',
        'schedule': crontab(minute=5),
    },
    'container-batch-dispatch': {
        'task': 'bookings.tasks.check_and_mark_batches',
        'schedule': crontab(minute=10),
    },
}


CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

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


# Add these settings for testing
if 'pytest' in sys.modules:
    DATABASES['default']['ATOMIC_REQUESTS'] = False
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True

# Add this near the top of settings.py
if 'pytest' in sys.argv[0]:
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = 'memory://'

# settings.py
DEFAULT_FROM_EMAIL = "no-reply@cargoghana.com"
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_FROM")            # e.g. "+1415xxxxxxx"
ADMIN_WHATSAPP = os.getenv("ADMIN_WHATSAPP")                   # e.g. "+233xxxxxxxx"


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
        # (or JWTAuthentication if you're using Simple JWT)
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],

    # — Default permissions —
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],

    # — Throttle classes —
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day'
    }
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


# Add this with your other settings
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')


# Google Analytics Configuration
# Meta Pixel Configuration
META_PIXEL_ID = os.getenv('META_PIXEL_ID')  # e.g. '123456789'
# Google Analytics Configuration
GA_MEASUREMENT_ID = os.getenv('GA_MEASUREMENT_ID')  # e.g. 'G-XXXXXXXXXX'


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://redis:6379/1'),
    }
}