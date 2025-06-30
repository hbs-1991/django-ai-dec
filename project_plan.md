# 📋 План разработки проекта AI DECLARANT

## 🎯 Этап 1: Настройка инфраструктуры и базового проекта (1-2 недели)

### 1.1 Инициализация проекта
- [ ] **Создание Django проекта**
  - Установка Django 5.0 LTS + DRF + необходимых зависимостей
  - Настройка структуры проекта с приложениями: `core`, `processing`, `users`, `api`
  - Конфигурация настроек для dev/prod окружений

- [ ] **Настройка БД PostgreSQL 16**
  - Docker-compose для локальной разработки
  - Миграции базовых моделей (User, ProcessingTask, HSCode)
  - Настройка Django-админки

- [ ] **Настройка Celery + Redis**
  - Конфигурация Celery для Django
  - Настройка Redis как брокер сообщений
  - Базовая задача для тестирования асинхронности

### 1.2 Базовая инфраструктура
- [ ] **Docker контейнеризация**
  - Dockerfile для Django приложения
  - docker-compose.yml для всех сервисов
  - Настройка volumes для файлов

- [ ] **CI/CD настройка**
  - GitHub Actions для автоматических тестов
  - Деплой на AWS ECS Fargate (staging окружение)
  - Базовые health-check endpoints

## 🗃️ Этап 2: Модели данных и API (1-2 недели)

### 2.1 Django модели
- [ ] **Модель ProcessingTask**
  ```python
  class ProcessingTask(models.Model):
      user = models.ForeignKey(User, on_delete=models.CASCADE)
      file_name = models.CharField(max_length=255)
      status = models.CharField(choices=STATUS_CHOICES)
      total_items = models.IntegerField()
      processed_items = models.IntegerField(default=0)
      created_at = models.DateTimeField(auto_now_add=True)
      celery_task_id = models.CharField(max_length=255, null=True)
  ```

- [ ] **Модель HSCode и ProductItem**
  ```python
  class HSCode(models.Model):
      code = models.CharField(max_length=10, unique=True)
      description = models.TextField()
      category = models.CharField(max_length=100)
      
  class ProductItem(models.Model):
      task = models.ForeignKey(ProcessingTask, on_delete=models.CASCADE)
      original_description = models.TextField()
      suggested_hs_code = models.ForeignKey(HSCode, on_delete=models.SET_NULL, null=True)
      confidence_score = models.FloatField()
      alternatives = models.JSONField(default=list)
      status = models.CharField(choices=ITEM_STATUS_CHOICES)
  ```

### 2.2 Django REST Framework API
- [ ] **ViewSets для основных операций**
  ```python
  class ProcessingTaskViewSet(ModelViewSet):
      # CRUD операции для задач обработки
      # POST /api/tasks/ - создание новой задачи
      # GET /api/tasks/{id}/ - получение статуса
  
  class ProductItemViewSet(ReadOnlyModelViewSet):
      # GET /api/tasks/{task_id}/items/ - список элементов
      # PATCH /api/items/{id}/ - обновление статуса/кода
  ```

- [ ] **Сериализаторы для API**
  - TaskCreateSerializer для загрузки файлов
  - TaskStatusSerializer для отслеживания прогресса
  - ProductItemSerializer с альтернативными кодами

## 🧠 Этап 3: AI агенты и Vector Store (2-3 недели)

### 3.1 OpenAI Vector Store настройка
- [ ] **Создание и наполнение векторной БД**
  ```python
  from openai import OpenAI
  
  client = OpenAI()
  
  # Создание vector store для HS кодов
  vector_store = client.beta.vector_stores.create(
      name="hs-codes-turkmenistan"
  )
  
  # Загрузка HS кодов в формате документов
  def upload_hs_codes_to_vector_store():
      # Парсинг официальных HS кодов Туркменистана
      # Создание embeddings для описаний товаров
  ```

### 3.2 AI агенты с openai-agents-python
- [ ] **Главный агент классификации**
  ```python
  from openai_agents import Agent, function_tool
  
  @function_tool
  def search_similar_hs_codes(product_description: str) -> list:
      """Поиск похожих HS кодов в векторной БД"""
      # Семантический поиск через OpenAI Vector Store
      
  @function_tool 
  def web_search_product_info(product_name: str) -> str:
      """Веб-поиск дополнительной информации о товаре"""
      # Интеграция с MCP brave-search
  
  hs_classifier_agent = Agent(
      name="HS Code Classifier",
      instructions="""
      Ты эксперт по классификации товаров согласно HS кодам Туркменистана.
      Анализируй описание товара и предлагай наиболее подходящий HS код.
      """,
      tools=[search_similar_hs_codes, web_search_product_info]
  )
  ```

- [ ] **Агент валидации и проверки**
  ```python
  validation_agent = Agent(
      name="HS Code Validator", 
      instructions="""
      Проверяй предложенные HS коды на соответствие описанию товара.
      Оцени уровень доверия от 0 до 100%.
      """,
      tools=[search_similar_hs_codes]
  )
  ```

### 3.3 Celery задачи для обработки
- [ ] **Асинхронная обработка файлов**
  ```python
  from celery import shared_task
  from django.db import transaction
  
  @shared_task(bind=True)
  def process_file_task(self, task_id):
      task = ProcessingTask.objects.get(id=task_id)
      
      # Парсинг Excel/CSV файла
      items = parse_uploaded_file(task.file_path)
      
      for i, item in enumerate(items):
          # Обработка через AI агентов
          result = hs_classifier_agent.run(
              f"Определи HS код для: {item.description}"
          )
          
          # Сохранение результата
          ProductItem.objects.create(
              task=task,
              original_description=item.description,
              suggested_hs_code=result.hs_code,
              confidence_score=result.confidence
          )
          
          # Обновление прогресса
          task.processed_items = i + 1
          task.save()
  ```

## 📁 Этап 4: Обработка файлов и парсинг (1-2 недели)

### 4.1 Загрузка и валидация файлов
- [ ] **Обработчики файлов**
  ```python
  import pandas as pd
  from django.core.files.storage import default_storage
  
  class FileProcessor:
      @staticmethod
      def validate_file(file):
          # Проверка размера, формата, структуры
          
      @staticmethod  
      def parse_excel(file_path):
          df = pd.read_excel(file_path)
          return df.to_dict('records')
          
      @staticmethod
      def parse_csv(file_path):
          df = pd.read_csv(file_path)
          return df.to_dict('records')
  ```

- [ ] **API endpoint для загрузки**
  ```python
  @api_view(['POST'])
  def upload_file(request):
      file = request.FILES['file']
      
      # Валидация
      if not FileProcessor.validate_file(file):
          return Response({'error': 'Invalid file'}, status=400)
      
      # Сохранение файла
      file_path = default_storage.save(f'uploads/{file.name}', file)
      
      # Создание задачи
      task = ProcessingTask.objects.create(
          user=request.user,
          file_name=file.name,
          status='pending'
      )
      
      # Запуск асинхронной обработки
      process_file_task.delay(task.id)
      
      return Response({'task_id': task.id})
  ```

### 4.2 Сопоставление колонок
- [ ] **Интеллектуальное определение колонок**
  ```python
  class ColumnMapper:
      COMMON_PATTERNS = {
          'description': ['описание', 'название', 'товар', 'product', 'description'],
          'category': ['категория', 'группа', 'category', 'group'],
          'quantity': ['количество', 'qty', 'количво'],
      }
      
      @classmethod
      def auto_map_columns(cls, df_columns):
          # Автоматическое сопоставление по паттернам
  ```

## 🎨 Этап 5: Streamlit Frontend (2-3 недели)

### 5.1 Основной интерфейс
- [ ] **Главная страница с загрузкой файлов**
  ```python
  import streamlit as st
  import requests
  
  st.title("🚢 AI DECLARANT - Классификация HS кодов")
  
  # Drag & drop файлов
  uploaded_files = st.file_uploader(
      "Загрузите Excel или CSV файлы",
      type=['xlsx', 'xls', 'csv'],
      accept_multiple_files=True,
      help="Максимум 1000 позиций на файл"
  )
  
  if uploaded_files:
      for file in uploaded_files:
          # Предпросмотр первых 5 строк
          preview_df = pd.read_excel(file, nrows=5)
          st.dataframe(preview_df)
          
          # Сопоставление колонок
          columns = st.multiselect(
              "Выберите колонку с описанием товара",
              options=preview_df.columns
          )
  ```

- [ ] **Страница статуса обработки**
  ```python
  def show_processing_status(task_id):
      # Периодическое обновление статуса
      placeholder = st.empty()
      
      while True:
          response = requests.get(f"http://api/tasks/{task_id}/")
          task = response.json()
          
          with placeholder.container():
              progress = task['processed_items'] / task['total_items']
              st.progress(progress)
              st.write(f"Обработано {task['processed_items']} из {task['total_items']}")
              
          if task['status'] == 'completed':
              break
              
          time.sleep(2)
  ```

### 5.2 Интерактивные результаты
- [ ] **Таблица результатов с редактированием**
  ```python
  def show_results(task_id):
      # Получение результатов через API
      items = requests.get(f"http://api/tasks/{task_id}/items/").json()
      
      df = pd.DataFrame(items)
      
      # Интерактивная таблица с возможностью редактирования
      edited_df = st.data_editor(
          df,
          column_config={
              "confidence_score": st.column_config.ProgressColumn(
                  "Уверенность", min_value=0, max_value=100
              ),
              "status": st.column_config.SelectboxColumn(
                  "Статус",
                  options=["confirmed", "needs_review", "rejected"]
              )
          },
          disabled=["original_description", "suggested_hs_code"]
      )
  ```

- [ ] **Фильтрация и экспорт**
  ```python
  # Фильтры
  confidence_filter = st.slider("Минимальная уверенность", 0, 100, 60)
  status_filter = st.multiselect("Статус", ["confirmed", "needs_review", "rejected"])
  
  # Кнопка экспорта
  if st.button("📥 Экспорт результатов"):
      excel_buffer = io.BytesIO()
      edited_df.to_excel(excel_buffer, index=False)
      
      st.download_button(
          label="Скачать Excel",
          data=excel_buffer.getvalue(),
          file_name=f"hs_codes_results_{task_id}.xlsx",
          mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      )
  ```

## 🔧 Этап 6: Интеграция и тестирование (2 недели)

### 6.1 Интеграция компонентов
- [ ] **Подключение Streamlit к Django API**
  - Настройка CORS для API
  - Аутентификация пользователей
  - Обработка ошибок и таймаутов

- [ ] **Мониторинг с Sentry**
  ```python
  import sentry_sdk
  from sentry_sdk.integrations.django import DjangoIntegration
  from sentry_sdk.integrations.celery import CeleryIntegration
  
  sentry_sdk.init(
      dsn="YOUR_SENTRY_DSN",
      integrations=[DjangoIntegration(), CeleryIntegration()],
      traces_sample_rate=0.1,
  )
  ```

### 6.2 Тестирование и оптимизация
- [ ] **Unit тесты для Django**
  ```python
  class ProcessingTaskTests(TestCase):
      def test_file_upload(self):
          # Тест загрузки файла
          
      def test_hs_code_classification(self):
          # Тест классификации через AI агентов
  ```

- [ ] **Нагрузочное тестирование**
  - Тест обработки 1000 позиций
  - Параллельная обработка нескольких файлов
  - Мониторинг производительности

## 🚀 Этап 7: Деплой и MVP запуск (1 неделя)

### 7.1 Production деплой
- [ ] **AWS ECS Fargate настройка**
  - Настройка ECS кластера и сервисов
  - Load Balancer и SSL сертификаты
  - Автоматическое масштабирование

- [ ] **Мониторинг production**
  - CloudWatch логи и метрики
  - Health checks для всех сервисов
  - Alerting при ошибках

### 7.2 Финальная подготовка
- [ ] **Наполнение Vector Store данными**
  - Загрузка официальных HS кодов Туркменистана
  - Тестирование точности классификации
  - Калибровка confidence scores

- [ ] **Документация и обучение**
  - Пользовательская документация
  - API документация через DRF
  - Инструкции по деплою

## 📈 Этап 8: Post-MVP улучшения (ongoing)

### 8.1 Улучшение AI агентов
- [ ] **Дополнительные MCP инструменты**
  - Интеграция с официальными таможенными БД
  - Инструменты для анализа товарных категорий
  - Multilingual поддержка (рус/туркм/англ)

### 8.2 Frontend миграция на Next.js
- [ ] **Современный веб-интерфейс**
  - Next.js 14 + TypeScript
  - shadcn/ui компоненты
  - Real-time обновления через WebSockets

---

## 🛠️ Технические детали реализации

### Структура Django проекта:
```
ai_declarant/
├── core/                    # Основные модели и утилиты
├── processing/              # Celery задачи и AI агенты  
├── api/                     # DRF API endpoints
├── users/                   # Пользователи и аутентификация
├── frontend_streamlit/      # Streamlit приложение
├── requirements.txt
├── docker-compose.yml
└── manage.py
```

### Ключевые зависимости:
```txt
Django==5.0.1
djangorestframework==3.14.0
celery==5.3.4
redis==5.0.1
pandas==2.1.4
openpyxl==3.1.2
openai==1.8.0
openai-agents-python==0.1.0
streamlit==1.29.0
psycopg2-binary==2.9.9
sentry-sdk==1.40.0
```

### Временные рамки и ресурсы:
- **Общее время разработки MVP:** 10-15 недель
- **Команда:** 2-3 разработчика (1 backend, 1 frontend, 1 DevOps/fullstack)
- **Критический путь:** Этапы 3-5 (AI агенты и интеграция)

### Ключевые риски и митигация:
1. **Точность AI классификации** - Тщательное тестирование и калибровка на реальных данных
2. **Производительность при 1000 позиций** - Параллельная обработка через Celery
3. **Интеграция OpenAI Vector Store** - Fallback на локальную векторную БД
4. **UX сложность** - Итеративное тестирование с пользователями

Этот план обеспечивает поэтапную разработку с учетом современных практик и изученных библиотек. Каждый этап может выполняться параллельно командой разработчиков.
