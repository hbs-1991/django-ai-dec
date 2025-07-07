"""
Конфигурация Celery для проекта AI DECLARANT
"""

import os
from celery import Celery
from django.conf import settings

# Устанавливаем модуль настроек Django по умолчанию для программы 'celery'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

app = Celery('ai_declarant')

# Используем строку здесь, это означает, что worker не должен сериализовать
# объект конфигурации для дочерних процессов.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Загружаем модули задач из всех зарегистрированных приложений Django.
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Отладочная задача для тестирования Celery"""
    print(f'Request: {self.request!r}')
    return 'Debug task completed!'

@app.task
def test_task():
    """Простая тестовая задача"""
    return 'Test task completed successfully!' 