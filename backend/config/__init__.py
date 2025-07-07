# Это гарантирует, что приложение Celery всегда импортируется
# когда Django запускается так, что shared_task будет использовать его:
from .celery import app as celery_app

__all__ = ('celery_app',)
