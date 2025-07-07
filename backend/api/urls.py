"""
URL маршруты для API
"""

from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import HSCodeViewSet, ProcessingTaskViewSet, ProductItemViewSet
from .health import HealthCheckView, ReadyCheckView, LivenessCheckView

# Создаем роутер для автоматической генерации URL
router = DefaultRouter()

# Регистрируем ViewSets
router.register(r'hs-codes', HSCodeViewSet, basename='hscode')
router.register(r'tasks', ProcessingTaskViewSet, basename='task')
router.register(r'items', ProductItemViewSet, basename='item')

urlpatterns = [
    path('', include(router.urls)),
    
    # Health Check endpoints
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('ready/', ReadyCheckView.as_view(), name='ready-check'),
    path('live/', LivenessCheckView.as_view(), name='liveness-check'),
]

# Доступные API endpoints:
"""
HS Коды:
GET /api/hs-codes/                      - Список всех HS кодов
GET /api/hs-codes/{id}/                 - Детали конкретного HS кода  
GET /api/hs-codes/search/?q=query       - Поиск HS кодов
GET /api/hs-codes/categories/           - Список категорий

Задачи обработки:
GET /api/tasks/                         - Список задач пользователя
POST /api/tasks/                        - Создать новую задачу (+ file)
GET /api/tasks/{id}/                    - Детали задачи
PATCH /api/tasks/{id}/                  - Обновить задачу
DELETE /api/tasks/{id}/                 - Удалить задачу
GET /api/tasks/{id}/status/             - Статус выполнения
POST /api/tasks/{id}/cancel/            - Отменить задачу
GET /api/tasks/{id}/items/              - Позиции товаров задачи
GET /api/tasks/{id}/export/             - Экспорт результатов

Позиции товаров:
GET /api/items/                         - Список позиций пользователя
GET /api/items/{id}/                    - Детали позиции
PATCH /api/items/{id}/                  - Обновить позицию (статус, комментарий)
POST /api/items/{id}/approve/           - Подтвердить предложенный код
POST /api/items/{id}/reject/            - Отклонить предложенный код
""" 