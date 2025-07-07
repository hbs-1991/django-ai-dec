"""
Настройки для разработки
"""

import os
from .base import *

# Загружаем переменные окружения из .env файла
from dotenv import load_dotenv
load_dotenv()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Database для разработки
# Проверяем наличие DATABASE_URL (Docker/production) или используем SQLite
DATABASE_URL = os.environ.get('DATABASE_URL', '')

# Принудительно используем SQLite для локальной разработки, если не Docker
USE_DOCKER = os.environ.get('USE_DOCKER', 'False').lower() == 'true'

if USE_DOCKER and DATABASE_URL.startswith('postgresql'):
    # PostgreSQL для Docker/production
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }
    print("🐳 Используется PostgreSQL (Docker)")
else:
    # SQLite для локальной разработки
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    print("💻 Используется SQLite (локальная разработка)")

# Отключаем CORS проверки для разработки
CORS_ALLOW_ALL_ORIGINS = True

# Добавляем debug toolbar
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    
    INTERNAL_IPS = [
        '127.0.0.1',
        'localhost',
    ]

# Логирование для разработки
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Email backend для разработки (выводит в консоль)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Celery настройки для разработки
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/1')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Celery для разработки - выполнение в реальном времени
CELERY_TASK_ALWAYS_EAGER = os.environ.get('CELERY_ALWAYS_EAGER', 'False').lower() == 'true'
CELERY_TASK_EAGER_PROPAGATES = True 