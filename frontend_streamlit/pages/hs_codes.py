"""
Страница справочника HS кодов
"""

import streamlit as st
import pandas as pd
from utils.api_client import APIClient



def get_categories(api: APIClient):
    """Получение списка категорий"""
    try:
        categories = api.get_hs_categories()
        return categories
    except Exception as e:
        st.error(f"Ошибка при получении категорий: {e}")
        return []

def show_search_results(api: APIClient, query: str, category_filter: str, sort_by: str):
    """Отображение результатов поиска"""
    
    try:
        # Выполняем поиск
        if query:
            results = api.search_hs_codes(query)
        else:
            # Получаем все коды
            response = api.get('/hs-codes/')
            results = response.get('results', []) if response else []
        
        if not results:
            st.warning("Ничего не найдено по вашему запросу")
            return
        
        # Применяем фильтр по категории
        if category_filter != "Все категории":
            results = [r for r in results if r.get('category') == category_filter]
        
        # Сортировка
        if sort_by == "По коду":
            results.sort(key=lambda x: x.get('code', ''))
        elif sort_by == "По названию":
            results.sort(key=lambda x: x.get('description', ''))
        elif sort_by == "По категории":
            results.sort(key=lambda x: x.get('category', ''))
        
        st.subheader(f"📋 Результаты поиска ({len(results)})")
        
        # Отображаем результаты
        for result in results:
            show_hs_code_card(result)
    
    except Exception as e:
        st.error(f"Ошибка при поиске: {e}")

def show_browse_interface(api: APIClient, category_filter: str, sort_by: str):
    """Интерфейс просмотра всех кодов"""
    
    st.subheader("📚 Обзор справочника")
    
    try:
        # Получаем все коды с пагинацией
        response = api.get('/hs-codes/')
        
        if not response:
            st.error("Не удалось загрузить справочник")
            return
        
        codes = response.get('results', [])
        total_count = response.get('count', 0)
        
        if not codes:
            st.info("Справочник пуст")
            return
        
        # Применяем фильтр по категории
        if category_filter != "Все категории":
            codes = [c for c in codes if c.get('category') == category_filter]
        
        # Сортировка
        if sort_by == "По коду":
            codes.sort(key=lambda x: x.get('code', ''))
        elif sort_by == "По названию":
            codes.sort(key=lambda x: x.get('description', ''))
        elif sort_by == "По категории":
            codes.sort(key=lambda x: x.get('category', ''))
        
        # Статистика
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📊 Всего кодов", total_count)
        
        with col2:
            st.metric("🔍 Показано", len(codes))
        
        with col3:
            unique_categories = len(set(c.get('category', '') for c in codes))
            st.metric("📁 Категорий", unique_categories)
        
        st.markdown("---")
        
        # Отображаем коды
        for code in codes:
            show_hs_code_card(code)
    
    except Exception as e:
        st.error(f"Ошибка при загрузке справочника: {e}")

def show_hs_code_card(hs_code):
    """Отображение карточки HS кода"""
    
    with st.container():
        col1, col2, col3 = st.columns([2, 3, 1])
        
        with col1:
            # Код HS
            st.markdown(f"### `{hs_code.get('code', 'N/A')}`")
        
        with col2:
            # Описание
            st.markdown(f"**{hs_code.get('description', 'Описание отсутствует')}**")
            
            # Категория
            category = hs_code.get('category', 'Не указана')
            subcategory = hs_code.get('subcategory', '')
            
            if subcategory and subcategory != 'Общая группа':
                st.caption(f"📁 {category} → {subcategory}")
            else:
                st.caption(f"📁 {category}")
        
        with col3:
            # Кнопка копирования
            if st.button("📋 Копировать", key=f"copy_{hs_code.get('id')}", help="Копировать код"):
                st.info(f"Код {hs_code.get('code')} скопирован!")
        
        # Дополнительная информация в развернутом виде
        with st.expander("ℹ️ Подробности", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                **Основная информация:**
                - Код: `{hs_code.get('code', 'N/A')}`
                - Категория: {hs_code.get('category', 'Не указана')}
                - Подкатегория: {hs_code.get('subcategory', 'Не указана')}
                - Статус: {'Активный' if hs_code.get('is_active', True) else 'Неактивный'}
                """)
            
            with col2:
                created_at = hs_code.get('created_at', '')
                updated_at = hs_code.get('updated_at', '')
                
                st.markdown(f"""
                **Метаинформация:**
                - ID: {hs_code.get('id', 'N/A')}
                - Создан: {format_date(created_at)}
                - Обновлен: {format_date(updated_at)}
                """)
            
            # Примеры товаров (если есть)
            st.markdown("**💡 Примеры товаров для этого кода:**")
            examples = get_code_examples(hs_code.get('code', ''))
            if examples:
                for example in examples:
                    st.write(f"• {example}")
            else:
                st.caption("Примеры товаров не найдены")
        
        st.markdown("---")

def get_code_examples(hs_code: str):
    """Получение примеров товаров для HS кода"""
    
    # Простые примеры на основе кода (можно расширить)
    examples_map = {
        '8703': [
            'Автомобили легковые',
            'Седан Toyota Camry',
            'Хэтчбек Volkswagen Golf',
            'Внедорожник BMW X5'
        ],
        '0901': [
            'Кофе натуральный в зернах',
            'Кофе арабика',
            'Кофе робуста',
            'Зеленый кофе'
        ],
        '6203': [
            'Костюмы мужские',
            'Брюки деловые',
            'Пиджаки классические',
            'Жилеты мужские'
        ],
        '8471': [
            'Компьютеры персональные',
            'Ноутбуки',
            'Планшетные компьютеры',
            'Серверы'
        ]
    }
    
    # Ищем по началу кода
    for code_prefix, examples in examples_map.items():
        if hs_code.startswith(code_prefix):
            return examples
    
    return []

def format_date(date_str: str) -> str:
    """Форматирование даты"""
    if not date_str:
        return "Не указано"
    
    try:
        from datetime import datetime
        if 'T' in date_str:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%d.%m.%Y')
    except:
        pass
    
    return date_str[:10] if len(date_str) > 10 else date_str

# Дополнительная секция с полезной информацией
def show_hs_info_section():
    """Отображение информационной секции о HS кодах"""
    
    st.markdown("---")
    st.subheader("ℹ️ О кодах ТН ВЭД")
    
    with st.expander("📖 Что такое коды ТН ВЭД?", expanded=False):
        st.markdown("""
        **Товарная номенклатура внешнеэкономической деятельности (ТН ВЭД)** — 
        это классификатор товаров, применяемый для таможенного оформления.
        
        **Структура кода:**
        - Первые 2 цифры — группа товаров
        - 3-4 цифры — товарная позиция  
        - 5-6 цифры — субпозиция
        - 7-8 цифры — подсубпозиция
        - 9-10 цифры — национальная подсубпозиция
        
        **Примеры:**
        - `87` — Средства наземного транспорта
        - `8703` — Автомобили легковые
        - `8703.10` — С искровым зажиганием, объем двигателя ≤ 1000 см³
        """)
    
    with st.expander("🎯 Как правильно выбрать код?", expanded=False):
        st.markdown("""
        **Принципы классификации:**
        
        1. **Материал изготовления** — из чего сделан товар
        2. **Функциональное назначение** — для чего предназначен
        3. **Степень обработки** — сырье, полуфабрикат или готовый товар
        4. **Конструктивные особенности** — форма, размер, технические характеристики
        
        **Рекомендации:**
        - Изучите описание товара в справочнике
        - Проверьте примеры товаров для выбранного кода
        - При сомнениях консультируйтесь с таможенным брокером
        - Используйте AI DECLARANT для автоматического подбора
        """)

# Добавляем информационную секцию в основную функцию
def show_main_content():
    """Основной контент страницы справочника HS кодов"""
    
    st.header("🔍 Справочник HS кодов")
    st.markdown("Поиск и просмотр кодов Товарной номенклатуры внешнеэкономической деятельности")
    
    # API клиент
    api = APIClient()
    
    # Поиск
    st.subheader("🔎 Поиск кодов")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input(
            "Введите код или описание товара:",
            placeholder="Например: 8703 или автомобиль",
            help="Поиск по коду HS, описанию товара или категории"
        )
    
    with col2:
        search_button = st.button("🔍 Найти", type="primary", use_container_width=True)
    
    # Фильтры
    col1, col2 = st.columns(2)
    
    with col1:
        # Получаем категории
        categories = get_categories(api)
        category_filter = st.selectbox(
            "Категория:",
            options=["Все категории"] + categories,
            index=0
        )
    
    with col2:
        sort_by = st.selectbox(
            "Сортировка:",
            options=["По коду", "По названию", "По категории"],
            index=0
        )
    
    # Выполнение поиска
    if search_query or search_button:
        show_search_results(api, search_query, category_filter, sort_by)
    else:
        show_browse_interface(api, category_filter, sort_by)

# Переопределяем основную функцию show()
def show():
    """Отображение страницы справочника HS кодов"""
    
    # Основной контент
    show_main_content()
    
    # Дополнительная информация
    show_hs_info_section() 