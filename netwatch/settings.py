"""
Django settings for netwatch project.
"""
import os
from pathlib import Path
from typing import List
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    'DJANGO_SECRET_KEY',
    'django-insecure-change-this-in-production-please'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS: List[str] = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,10.18.70.71').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # Local apps
    'apps.accounts',
    'apps.inventory',
    'apps.monitoring',
    'apps.dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # WhiteNoise for static file serving
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'netwatch.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'netwatch.wsgi.application'

# Database
# Use DATABASE_URL (Heroku), PostgreSQL, or SQLite (local dev)
if os.getenv('DATABASE_URL'):
    # Heroku PostgreSQL
    DATABASES = {
        'default': dj_database_url.config(
            default=os.getenv('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASE_ENGINE = os.getenv('DATABASE_ENGINE', 'sqlite')
    
    if DATABASE_ENGINE == 'postgresql':
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.getenv('DB_NAME', 'netwatch'),
                'USER': os.getenv('DB_USER', 'postgres'),
                'PASSWORD': os.getenv('DB_PASSWORD', ''),
                'HOST': os.getenv('DB_HOST', 'localhost'),
                'PORT': os.getenv('DB_PORT', '5432'),
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }

# Password validation
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

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.getenv('TIME_ZONE', 'UTC')
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'  # WhiteNoise compression for Heroku

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Cache Configuration for local development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Celery Configuration
# Celery/Redis configuration with Heroku rediss:// support
def _format_redis_url(url: str) -> str:
    """Add ssl_cert_reqs to rediss:// URLs if missing (for Heroku Redis)."""
    if not url:
        return url
    if url.startswith('rediss://') and 'ssl_cert_reqs' not in url:
        # Append ssl_cert_reqs=CERT_NONE to avoid SSL verification issues
        separator = '&' if '?' in url else '?'
        url = f"{url}{separator}ssl_cert_reqs=CERT_NONE"
    return url

# For local development, use eager execution if no explicit broker is set
if os.getenv('CELERY_BROKER_URL'):
    _broker_url = os.getenv('CELERY_BROKER_URL')
    _result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    CELERY_BROKER_URL = _format_redis_url(_broker_url)
    CELERY_RESULT_BACKEND = _format_redis_url(_result_backend)
    CELERY_TASK_ALWAYS_EAGER = False
else:
    # Local development: use eager execution to run tasks synchronously
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = 'cache+memory://'
    CELERY_CACHE_BACKEND = 'memory'
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
 
# Redis TLS options (required for rediss:// in local workers)
import ssl
if (isinstance(CELERY_BROKER_URL, str) and CELERY_BROKER_URL.startswith('rediss://')):
    CELERY_BROKER_USE_SSL = {
        'ssl_cert_reqs': ssl.CERT_NONE,
    }
    CELERY_BROKER_TRANSPORT_OPTIONS = {
        'ssl_cert_reqs': ssl.CERT_NONE,
    }
if (isinstance(CELERY_RESULT_BACKEND, str) and CELERY_RESULT_BACKEND.startswith('rediss://')):
    CELERY_REDIS_BACKEND_USE_SSL = {
        'ssl_cert_reqs': ssl.CERT_NONE,
    }
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
# Use threads pool on Windows to avoid multiprocessing issues
CELERY_WORKER_POOL = 'threads'
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_BEAT_SCHEDULE = {
    'run-monitoring-checks': {
        'task': 'apps.monitoring.tasks.run_all_monitoring_checks',
        'schedule': 60.0,  # Run every 60 seconds
    },
    'cleanup-old-results': {
        'task': 'apps.monitoring.tasks.cleanup_old_check_results',
        'schedule': 3600.0,  # Run every hour
    },
    'cleanup-old-data': {
        'task': 'apps.monitoring.tasks.cleanup_old_data',
        'schedule': 86400.0,  # Run daily
    },
}

# Email Configuration for Alerts
EMAIL_BACKEND = os.getenv(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'netwatch@example.com')
ALERT_EMAIL_RECIPIENTS = os.getenv('ALERT_EMAIL_RECIPIENTS', '').split(',')

# ChatWarning Integration Configuration
# Set these environment variables on Heroku:
# heroku config:set ALERT_CHAT_BASE_URL='https://chatwarning.herokuapp.com'
# heroku config:set ALERT_CHAT_USER='admin'
# heroku config:set ALERT_CHAT_PASS='your-password'
ALERT_CHAT_BASE_URL = os.getenv('ALERT_CHAT_BASE_URL', '')
ALERT_CHAT_USER = os.getenv('ALERT_CHAT_USER', '')
ALERT_CHAT_PASS = os.getenv('ALERT_CHAT_PASS', '')
ALERT_SEND_STATUS_EVERY_CHECK = os.getenv('ALERT_SEND_STATUS_EVERY_CHECK', 'False').lower() in ('true', '1', 'yes')
ALERT_STATUS_ALERT_ONCE_PER_STATUS = os.getenv('ALERT_STATUS_ALERT_ONCE_PER_STATUS', 'False').lower() in ('true', '1', 'yes')

# Alert Thresholds for Device Monitoring
# CPU usage threshold (percentage) - alert when exceeded
ALERT_CPU_THRESHOLD = float(os.getenv('ALERT_CPU_THRESHOLD', '85'))

# Memory/RAM usage threshold (percentage) - alert when exceeded
ALERT_MEMORY_THRESHOLD = float(os.getenv('ALERT_MEMORY_THRESHOLD', '85'))

# Disk/Storage usage threshold (percentage) - alert when exceeded
ALERT_DISK_THRESHOLD = float(os.getenv('ALERT_DISK_THRESHOLD', '90'))

# Device uptime threshold (days) - alert when exceeded (to remind reboot)
ALERT_UPTIME_THRESHOLD_DAYS = int(os.getenv('ALERT_UPTIME_THRESHOLD_DAYS', '30'))

# Send agent state change alerts (UP/DOWN). Disabled by default to avoid extra noise.
ALERT_SEND_AGENT_ALERTS = os.getenv('ALERT_SEND_AGENT_ALERTS', 'False').lower() in ('true', '1', 'yes')

# Agent freshness for status determination (minutes)
AGENT_FRESH_MINUTES = int(os.getenv('AGENT_FRESH_MINUTES', '10'))

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'queue': {
            # Fallback to console in environments without a QueueHandler queue (e.g., Heroku build/collectstatic)
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'netwatch.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'queue'],
        'level': os.getenv('LOG_LEVEL', 'INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'queue'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'queue'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
(BASE_DIR / 'logs').mkdir(exist_ok=True)

# Configure QueueListener to process logs in background
import logging.handlers
import queue as queue_module
import threading

log_queue = queue_module.Queue()
queue_handler = logging.handlers.RotatingFileHandler(
    BASE_DIR / 'logs' / 'netwatch.log',
    maxBytes=10485760,
    backupCount=5
)
queue_handler.setFormatter(logging.Formatter('{levelname} {asctime} {module} {message}', style='{'))

listener = logging.handlers.QueueListener(log_queue, queue_handler, respect_handler_level=True)
listener.start()

# Store listener for cleanup
import atexit
atexit.register(listener.stop)

# Login configuration
# Point to the namespaced accounts login view
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard:index'

# Security settings for production (Heroku)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_SECURITY_POLICY = {
        'default-src': ("'self'", 'https:'),
    }
