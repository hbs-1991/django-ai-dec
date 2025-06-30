# Создание README.md
@"
# 🚢 AI DECLARANT

Автоматическая классификация товаров по кодам ТН ВЭД для таможенных брокеров Туркменистана.

## 🎯 Описание

AI DECLARANT - это веб-приложение, которое использует искусственный интеллект для автоматического определения кодов ТН ВЭД (Harmonized System) товаров на основе их описания. Система обрабатывает до 1000 позиций из Excel/CSV файлов и предоставляет рекомендации с уровнем доверия.

## 🛠️ Технический стек

- **Backend**: Django 5.0 LTS + Django REST Framework
- **Database**: PostgreSQL 16
- **Task Queue**: Celery 5 + Redis
- **AI**: OpenAI Agents + Vector Store
- **Frontend**: Streamlit (MVP) → Next.js (будущее)
- **Infrastructure**: Docker, AWS ECS Fargate

## 🚀 Быстрый старт

### Требования
- Python 3.12+
- Docker & Docker Compose
- Redis
- PostgreSQL 16

### Установка

1. Клонирование репозитория:
``````bash
git clone https://github.com/your-org/ai-declarant.git
cd ai-declarant
``````

2. Создание окружения:
``````bash
python -m venv venv
venv\Scripts\activate     # Windows
``````

3. Установка зависимостей:
``````bash
pip install -r requirements.txt
``````

4. Настройка переменных окружения:
``````bash
copy .env.example .env
# Отредактируйте .env файл с вашими настройками
``````

5. Запуск через Docker:
``````bash
docker-compose up -d
``````

## 📁 Структура проекта

``````
ai-declarant/
├── backend/                 # Django приложение
│   ├── core/               # Основные модели
│   ├── processing/         # AI агенты и Celery задачи
│   ├── users/              # Пользователи
│   ├── api/                # REST API
│   └── config/             # Настройки Django
├── frontend_streamlit/     # Streamlit интерфейс
├── docker/                 # Docker конфигурации
├── docs/                   # Документация
├── scripts/                # Скрипты развертывания
└── requirements.txt
``````

## 📚 Документация

- [API Документация](docs/API.md)
- [Руководство по развертыванию](docs/DEPLOYMENT.md)
- [Пользовательское руководство](docs/USER_GUIDE.md)

## 🤝 Участие в разработке

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'Add some AmazingFeature'`)
4. Push в branch (`git push origin feature/AmazingFeature`)
5. Создайте Pull Request

## 📝 Лицензия

Этот проект лицензирован под MIT License - см. [LICENSE](LICENSE) файл.

## 📞 Контакты

- Email: support@ai-declarant.com
- GitHub: [https://github.com/your-org/ai-declarant](https://github.com/your-org/ai-declarant)
"@ | Out-File -FilePath "README.md" -Encoding utf8

Write-Host "✅ README.md создан" -ForegroundColor Green
```

## 🐳 Создание Docker файлов

```powershell
# Создание Dockerfile для backend
@"
FROM python:3.12-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements и установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY backend/ .

# Создание пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app
USER app

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
"@ | Out-File -FilePath "docker\Dockerfile.backend" -Encoding utf8

# Создание Dockerfile для frontend
@"
FROM python:3.12-slim

WORKDIR /app

# Установка Streamlit и зависимостей
RUN pip install streamlit pandas requests plotly

# Копирование frontend кода
COPY frontend_streamlit/ .

# Создание пользователя
RUN useradd --create-home --shell /bin/bash app
USER app

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
"@ | Out-File -FilePath "docker\Dockerfile.frontend" -Encoding utf8

Write-Host "✅ Docker файлы созданы" -ForegroundColor Green
```

## 🔄 Финальная инициализация Git

```powershell
# Добавление всех файлов в git
git add .

# Проверка статуса
git status

# Первый коммит
git commit -m "🎉 Initial project setup for AI DECLARANT

- Created complete project structure
- Added Django backend with core, processing, users, api apps  
- Added Streamlit frontend structure
- Configured Docker setup with PostgreSQL and Redis
- Added requirements.txt with all dependencies
- Created comprehensive README.md
- Set up .gitignore for Python/Django project
"

Write-Host "✅ Git репозиторий инициализирован!" -ForegroundColor Green
Write-Host "📁 Структура проекта AI DECLARANT готова к разработке!" -ForegroundColor Cyan
```

## 📊 Проверка созданной структуры

```powershell
# Показать созданную структуру
Get-ChildItem -Recurse -Directory | Select-Object FullName

Write-Host "`n📋 Следующие шаги:" -ForegroundColor Yellow
Write-Host "1. Настройте .env файл с вашими ключами API" -ForegroundColor White
Write-Host "2. Запустите: docker-compose up -d" -ForegroundColor White  
Write-Host "3. Начните разработку согласно project_plan.md" -ForegroundColor White
```

Теперь команды адаптированы для PowerShell и должны работать корректно на Windows! Основная проблема была в использовании Unix-синтаксиса `{backend/{core,processing}}` вместо PowerShell командлетов.