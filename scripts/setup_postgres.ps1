# PowerShell скрипт для настройки PostgreSQL для AI DECLARANT
# Выполните этот скрипт от имени администратора

Write-Host "🚀 Настройка PostgreSQL для AI DECLARANT" -ForegroundColor Green

# Параметры базы данных
$DB_NAME = "ai_declarant_db"
$DB_USER = "ai_declarant"
$DB_PASSWORD = "password123"
$DB_HOST = "localhost"
$DB_PORT = "5432"

Write-Host "`n📋 Параметры подключения:" -ForegroundColor Yellow
Write-Host "База данных: $DB_NAME"
Write-Host "Пользователь: $DB_USER"
Write-Host "Пароль: $DB_PASSWORD"
Write-Host "Хост: $DB_HOST"
Write-Host "Порт: $DB_PORT"

# Проверяем установлен ли PostgreSQL
Write-Host "`n🔍 Проверка установки PostgreSQL..." -ForegroundColor Blue

try {
    $psqlVersion = & psql --version
    Write-Host "✅ PostgreSQL найден: $psqlVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ PostgreSQL не найден!" -ForegroundColor Red
    Write-Host "📥 Скачайте и установите PostgreSQL с https://www.postgresql.org/download/windows/" -ForegroundColor Yellow
    Write-Host "🔧 Убедитесь что psql добавлен в PATH" -ForegroundColor Yellow
    exit 1
}

# Создаем базу данных и пользователя
Write-Host "`n🗄️ Создание базы данных и пользователя..." -ForegroundColor Blue

$sqlCommands = @"
-- Создание пользователя
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';

-- Создание базы данных
CREATE DATABASE $DB_NAME OWNER $DB_USER;

-- Предоставление прав
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
ALTER USER $DB_USER CREATEDB;

-- Подключение к базе данных
\c $DB_NAME

-- Предоставление прав на схему public
GRANT ALL ON SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;

\q
"@

# Записываем SQL команды во временный файл
$tempSqlFile = [System.IO.Path]::GetTempFileName() + ".sql"
$sqlCommands | Out-File -FilePath $tempSqlFile -Encoding UTF8

Write-Host "📝 SQL команды записаны в: $tempSqlFile" -ForegroundColor Gray

# Выполняем SQL команды
Write-Host "🔧 Выполнение SQL команд..." -ForegroundColor Blue

try {
    # Подключаемся к PostgreSQL как superuser
    Write-Host "🔑 Введите пароль для пользователя postgres:" -ForegroundColor Yellow
    & psql -U postgres -h $DB_HOST -p $DB_PORT -f $tempSqlFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ База данных успешно создана!" -ForegroundColor Green
    } else {
        Write-Host "❌ Ошибка при создании базы данных" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Ошибка подключения к PostgreSQL: $_" -ForegroundColor Red
    exit 1
} finally {
    # Удаляем временный файл
    Remove-Item $tempSqlFile -ErrorAction SilentlyContinue
}

# Проверяем подключение
Write-Host "`n🧪 Проверка подключения к созданной базе данных..." -ForegroundColor Blue

try {
    $env:PGPASSWORD = $DB_PASSWORD
    $result = & psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME -c "SELECT version();"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Подключение к базе данных успешно!" -ForegroundColor Green
    } else {
        Write-Host "❌ Ошибка подключения к базе данных" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Ошибка проверки подключения: $_" -ForegroundColor Red
} finally {
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
}

# Создаем файл .env для Django
Write-Host "`n📄 Создание файла .env для Django..." -ForegroundColor Blue

$envContent = @"
# Django Settings
SECRET_KEY=django-insecure-change-me-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL)
DATABASE_URL=postgresql://$DB_USER`:$DB_PASSWORD@$DB_HOST`:$DB_PORT/$DB_NAME

# Celery & Redis (будет настроено позже)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Environment
USE_DOCKER=False

# OpenAI (для будущего использования)
# OPENAI_API_KEY=your-openai-api-key

# Email (для уведомлений)
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=your-email@gmail.com
# EMAIL_HOST_PASSWORD=your-app-password
"@

$envFile = "backend\.env"
$envContent | Out-File -FilePath $envFile -Encoding UTF8

Write-Host "✅ Файл .env создан: $envFile" -ForegroundColor Green

Write-Host "`n🎉 Настройка PostgreSQL завершена!" -ForegroundColor Green
Write-Host "`n📋 Следующие шаги:" -ForegroundColor Yellow
Write-Host "1. cd backend" -ForegroundColor Gray
Write-Host "2. python manage.py migrate" -ForegroundColor Gray
Write-Host "3. python manage.py createsuperuser" -ForegroundColor Gray
Write-Host "4. python manage.py runserver" -ForegroundColor Gray

Write-Host "`n🔗 Строка подключения:" -ForegroundColor Cyan
Write-Host "postgresql://$DB_USER`:$DB_PASSWORD@$DB_HOST`:$DB_PORT/$DB_NAME" -ForegroundColor White 