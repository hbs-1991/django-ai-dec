# API Endpoints AI DECLARANT

## Базовая информация

**Базовый URL:** `http://127.0.0.1:8000/api/`

**Аутентификация:** Django Session Authentication / Token Authentication

**Формат ответов:** JSON

## Health Check Endpoints

### GET /api/health/
Полная проверка состояния системы

**Ответ:**
```json
{
  "status": "healthy|unhealthy",
  "timestamp": "2025-06-30T12:27:02.454643",
  "components": {
    "database": {"status": "healthy", "details": "..."},
    "redis": {"status": "healthy|unhealthy", "error": "..."},
    "celery": {"status": "healthy|unhealthy", "error": "..."},
    "filesystem": {"status": "healthy|warning", "details": "..."}
  }
}
```

### GET /api/ready/
Проверка готовности к обслуживанию

### GET /api/live/
Проверка жизнеспособности приложения

## HS Коды API

### GET /api/hs-codes/
Список всех активных HS кодов с пагинацией

**Параметры запроса:**
- `page` - номер страницы
- `page_size` - размер страницы

**Ответ:**
```json
{
  "count": 4,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "code": "8703.10.00",
      "description": "Автомобили легковые",
      "category": "Транспорт",
      "subcategory": "Общая группа",
      "is_active": true,
      "created_at": "2025-06-30T13:12:25.552833+05:00",
      "updated_at": "2025-06-30T13:12:25.552855+05:00"
    }
  ]
}
```

### GET /api/hs-codes/{id}/
Детали конкретного HS кода

### GET /api/hs-codes/search/?q={query}
Поиск HS кодов по коду, описанию или категории

**Параметры запроса:**
- `q` - поисковый запрос

**Ответ:**
```json
{
  "results": [
    {
      "id": 1,
      "code": "8703.10.00",
      "description": "Автомобили легковые"
    }
  ]
}
```

### GET /api/hs-codes/categories/
Список всех категорий HS кодов

**Ответ:**
```json
{
  "categories": ["Транспорт", "Одежда", "Продукты"]
}
```

## Задачи обработки файлов

### GET /api/tasks/
Список задач текущего пользователя

🔒 **Требует аутентификации**

### POST /api/tasks/
Создание новой задачи обработки файла

🔒 **Требует аутентификации**

**Тело запроса:** `multipart/form-data`
- `file` - Excel или CSV файл (макс. 10MB)

**Ответ:**
```json
{
  "id": 1,
  "user": "admin2",
  "file_name": "products.xlsx",
  "status": "pending",
  "total_items": 0,
  "processed_items": 0,
  "progress_percent": 0.0,
  "celery_task_id": "abc-123",
  "created_at": "2025-06-30T12:00:00+05:00"
}
```

### GET /api/tasks/{id}/
Детали задачи

### GET /api/tasks/{id}/status/
Статус выполнения задачи

**Ответ:**
```json
{
  "id": 1,
  "status": "processing|completed|failed",
  "total_items": 100,
  "processed_items": 45,
  "progress_percent": 45.0,
  "error_message": null
}
```

### POST /api/tasks/{id}/cancel/
Отмена выполнения задачи

### GET /api/tasks/{id}/items/
Позиции товаров для задачи с пагинацией

**Параметры запроса:**
- `page`, `page_size` - пагинация  
- `status` - фильтр по статусу (`pending`, `processed`, `confirmed`, `needs_review`)

### GET /api/tasks/{id}/export/?format=excel
Экспорт результатов (TODO)

## Позиции товаров

### GET /api/items/
Список позиций товаров пользователя

🔒 **Требует аутентификации**

### GET /api/items/{id}/
Детали позиции товара

### PATCH /api/items/{id}/
Обновление позиции товара

**Тело запроса:**
```json
{
  "status": "confirmed|needs_review",
  "user_comment": "Комментарий пользователя",
  "final_hs_code_id": 123
}
```

### POST /api/items/{id}/approve/
Подтвердить предложенный AI HS код

### POST /api/items/{id}/reject/
Отклонить предложенный AI HS код

**Тело запроса:**
```json
{
  "comment": "Причина отклонения"
}
```

## Коды ошибок

- `200` - Успешно
- `201` - Создано
- `400` - Неверный запрос
- `401` - Не авторизован
- `403` - Доступ запрещен
- `404` - Не найдено
- `500` - Внутренняя ошибка сервера
- `503` - Сервис недоступен

## Примеры использования

### Создание задачи обработки файла

```bash
curl -X POST http://127.0.0.1:8000/api/tasks/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "file=@products.xlsx"
```

### Поиск HS кода

```bash
curl "http://127.0.0.1:8000/api/hs-codes/search/?q=автомобиль"
```

### Проверка статуса задачи

```bash
curl http://127.0.0.1:8000/api/tasks/1/status/
```

## Статусы позиций товаров

- `pending` - Ожидает обработки
- `processed` - Обработано AI
- `confirmed` - Подтверждено пользователем  
- `needs_review` - Требует проверки

## Уведомления

Система поддерживает WebSocket уведомления о прогрессе обработки задач (будет реализовано позже). 