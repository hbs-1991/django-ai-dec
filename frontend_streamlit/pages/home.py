"""
Главная страница AI DECLARANT
"""

import streamlit as st
import requests
from utils.api_client import APIClient

def show():
    """Отображение главной страницы"""
    
    # Приветствие
    st.markdown("""
    ## 👋 Добро пожаловать в AI DECLARANT!
    
    Система автоматического определения кодов ТН ВЭД для таможенных брокеров Туркменистана.
    Загружайте Excel или CSV файлы с товарами и получайте точные коды классификации.
    """)
    
    # Статистика системы
    col1, col2, col3, col4 = st.columns(4)
    
    # Получаем статистику через API
    api = APIClient()
    
    with col1:
        st.metric(
            label="📋 HS Кодов в базе",
            value=get_hs_codes_count(),
            help="Количество HS кодов в справочнике"
        )
    
    with col2:
        st.metric(
            label="⚡ Статус API",
            value=get_api_status(),
            help="Состояние REST API сервера"
        )
    
    with col3:
        st.metric(
            label="🔄 Активных задач",
            value="0",
            help="Задач в обработке"
        )
    
    with col4:
        st.metric(
            label="✅ Обработано сегодня",
            value="0",
            help="Товарных позиций за сегодня"
        )
    
    st.markdown("---")
    
    # Инструкция по использованию
    st.subheader("🚀 Как начать работу")
    
    with st.expander("📖 Пошаговая инструкция", expanded=True):
        st.markdown("""
        ### Шаг 1: Подготовьте файл
        - Используйте Excel (.xlsx, .xls) или CSV формат
        - Максимальный размер файла: **10 MB**
        - Максимальное количество позиций: **1000**
        - Обязательные колонки: наименование товара, количество, единица измерения
        
        ### Шаг 2: Загрузите файл
        - Перейдите в раздел "📤 Загрузка файлов"
        - Выберите файл или перетащите его в область загрузки
        - Нажмите кнопку "Обработать"
        
        ### Шаг 3: Отследите прогресс
        - Следите за статусом в разделе "📊 Мои задачи"
        - Получите уведомление о завершении обработки
        
        ### Шаг 4: Проверьте результаты
        - Просмотрите предложенные HS коды в разделе "📋 Результаты"
        - При необходимости отредактируйте или замените коды
        - Экспортируйте финальный результат
        """)
    
    # Примеры поддерживаемых форматов
    st.subheader("📄 Поддерживаемые форматы файлов")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📊 Excel файлы:**
        - .xlsx (рекомендуется)
        - .xls (старый формат)
        
        **📝 CSV файлы:**
        - .csv с разделителем запятая
        - UTF-8 кодировка
        """)
    
    with col2:
        st.markdown("""
        **📋 Обязательные колонки:**
        - Наименование товара
        - Количество
        - Единица измерения
        
        **🔧 Дополнительные колонки:**
        - Страна происхождения
        - Стоимость
        - Описание
        """)
    
    # Примеры HS кодов
    st.subheader("🔍 Примеры HS кодов")
    
    # Получаем несколько примеров из API
    examples = get_hs_codes_examples()
    
    if examples:
        for example in examples:
            with st.container():
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.code(example.get('code', 'N/A'))
                with col2:
                    st.write(f"**{example.get('description', 'Описание не найдено')}**")
                    st.caption(f"Категория: {example.get('category', 'Не указана')}")
    else:
        st.info("Примеры HS кодов будут загружены после подключения к API")
    
    # Контактная информация
    st.markdown("---")
    st.subheader("📞 Поддержка")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🛠️ Техническая поддержка:**
        - Email: support@ai-declarant.tm
        - Telegram: @ai_declarant_bot
        - Часы работы: 9:00 - 18:00 (пн-пт)
        """)
    
    with col2:
        st.markdown("""
        **📚 Документация:**
        - [Руководство пользователя](docs/USER_GUIDE.md)
        - [API документация](docs/API_ENDPOINTS.md)
        - [FAQ и решение проблем](docs/FAQ.md)
        """)

def get_hs_codes_count():
    """Получает количество HS кодов из API"""
    try:
        api = APIClient()
        response = api.get('/hs-codes/')
        if response:
            return response.get('count', 'N/A')
    except:
        pass
    return "Нет данных"

def get_api_status():
    """Проверяет статус API"""
    try:
        api = APIClient()
        response = api.get('/live/')
        if response and response.get('status') == 'alive':
            return "🟢 Работает"
    except:
        pass
    return "🔴 Недоступен"

def get_hs_codes_examples():
    """Получает примеры HS кодов"""
    try:
        api = APIClient()
        response = api.get('/hs-codes/')
        if response and response.get('results'):
            return response['results'][:3]  # Первые 3 примера
    except:
        pass
    return [] 