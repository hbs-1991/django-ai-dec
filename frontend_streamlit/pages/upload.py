"""
Страница загрузки файлов
"""

import streamlit as st
import pandas as pd
from utils.api_client import APIClient
from utils.file_utils import validate_file, get_file_preview
import time

def show():
    """Отображение страницы загрузки файлов"""
    
    st.header("📤 Загрузка файлов для обработки")
    st.markdown("Загрузите Excel или CSV файл с товарами для автоматического определения HS кодов")
    
    # Инструкции
    with st.expander("📋 Требования к файлу", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **📄 Поддерживаемые форматы:**
            - Excel (.xlsx, .xls)
            - CSV (.csv)
            
            **📏 Ограничения:**
            - Максимальный размер: 10 MB
            - Максимальное количество строк: 1000
            """)
        
        with col2:
            st.markdown("""
            **📋 Обязательные колонки:**
            - Наименование товара
            - Количество
            - Единица измерения
            
            **🔧 Дополнительные колонки (опционально):**
            - Страна происхождения
            - Стоимость
            """)
    
    # Основная область загрузки
    uploaded_file = st.file_uploader(
        "Выберите файл или перетащите его сюда",
        type=['xlsx', 'xls', 'csv'],
        help="Поддерживаются Excel и CSV файлы размером до 10 MB"
    )
    
    if uploaded_file is not None:
        # Валидация файла
        validation_result = validate_file(uploaded_file)
        
        if validation_result['valid']:
            st.success(f"✅ Файл '{uploaded_file.name}' успешно загружен")
            
            # Информация о файле
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📄 Размер файла", f"{uploaded_file.size / 1024:.1f} KB")
            
            with col2:
                st.metric("📋 Тип файла", uploaded_file.type)
            
            with col3:
                if validation_result.get('rows'):
                    st.metric("📊 Строк данных", validation_result['rows'])
            
            # Предварительный просмотр
            st.subheader("👀 Предварительный просмотр")
            
            try:
                preview_df = get_file_preview(uploaded_file)
                if preview_df is not None and not preview_df.empty:
                    st.dataframe(
                        preview_df.head(10),
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    if len(preview_df) > 10:
                        st.info(f"Показаны первые 10 строк из {len(preview_df)}")
                    
                    # Проверка колонок
                    st.subheader("🔍 Анализ колонок")
                    analyze_columns(preview_df)
                    
                else:
                    st.error("Не удалось прочитать файл или файл пуст")
                    return
                    
            except Exception as e:
                st.error(f"Ошибка при чтении файла: {e}")
                return
            
            # Настройки обработки
            st.subheader("⚙️ Настройки обработки")
            
            col1, col2 = st.columns(2)
            
            with col1:
                auto_approve = st.checkbox(
                    "Автоматически подтверждать коды с высокой уверенностью (>90%)",
                    value=True,
                    help="Коды с confidence score выше 90% будут автоматически подтверждены"
                )
            
            with col2:
                email_notification = st.checkbox(
                    "Отправить email уведомление при завершении",
                    value=False,
                    help="Получить уведомление на email когда обработка завершится"
                )
            
            # Кнопка обработки
            st.markdown("---")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                if st.button(
                    "🚀 Начать обработку",
                    type="primary",
                    use_container_width=True,
                    help="Запустить обработку файла через AI DECLARANT"
                ):
                    process_file(uploaded_file, auto_approve, email_notification)
        
        else:
            # Показываем ошибки валидации
            st.error("❌ Файл не прошел валидацию:")
            for error in validation_result['errors']:
                st.error(f"• {error}")
    
    else:
        # Показываем примеры файлов когда ничего не загружено
        show_file_examples()

def analyze_columns(df):
    """Анализ колонок загруженного файла"""
    
    columns = df.columns.tolist()
    
    # Определяем типы колонок
    required_cols = {
        'name': [],
        'quantity': [],
        'unit': []
    }
    
    optional_cols = {
        'country': [],
        'price': [],
        'description': []
    }
    
    # Простая эвристика для определения колонок
    for col in columns:
        col_lower = col.lower().strip()
        
        # Наименование товара
        if any(word in col_lower for word in ['наименование', 'товар', 'продукт', 'name', 'product']):
            required_cols['name'].append(col)
        # Количество
        elif any(word in col_lower for word in ['количество', 'qty', 'quantity', 'кол-во']):
            required_cols['quantity'].append(col)
        # Единица измерения
        elif any(word in col_lower for word in ['единица', 'ед', 'unit', 'мера']):
            required_cols['unit'].append(col)
        # Страна
        elif any(word in col_lower for word in ['страна', 'country', 'происхождение']):
            optional_cols['country'].append(col)
        # Цена
        elif any(word in col_lower for word in ['цена', 'стоимость', 'price', 'cost']):
            optional_cols['price'].append(col)
        # Описание
        elif any(word in col_lower for word in ['описание', 'description', 'комментарий']):
            optional_cols['description'].append(col)
    
    # Отображаем результаты анализа
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔴 Обязательные колонки:**")
        for field, cols in required_cols.items():
            status = "✅" if cols else "❌"
            field_name = {
                'name': 'Наименование товара',
                'quantity': 'Количество',
                'unit': 'Единица измерения'
            }[field]
            
            if cols:
                st.success(f"{status} {field_name}: {', '.join(cols)}")
            else:
                st.error(f"{status} {field_name}: не найдено")
    
    with col2:
        st.markdown("**🟡 Дополнительные колонки:**")
        for field, cols in optional_cols.items():
            if cols:
                field_name = {
                    'country': 'Страна происхождения',
                    'price': 'Цена/стоимость',
                    'description': 'Описание'
                }[field]
                st.info(f"✅ {field_name}: {', '.join(cols)}")
    
    # Проверяем все ли обязательные колонки найдены
    missing_required = [field for field, cols in required_cols.items() if not cols]
    
    if missing_required:
        st.warning(f"⚠️ Не найдены обязательные колонки. Обработка может работать некорректно.")
    else:
        st.success("✅ Все обязательные колонки найдены!")

def process_file(uploaded_file, auto_approve, email_notification):
    """Обработка загруженного файла"""
    
    # Создаем прогресс бар
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("📤 Загрузка файла на сервер...")
        progress_bar.progress(25)
        
        # Отправляем файл через API
        api = APIClient()
        
        # Сбрасываем указатель файла в начало
        uploaded_file.seek(0)
        
        result = api.upload_file(uploaded_file)
        
        if result:
            task_id = result.get('id')
            progress_bar.progress(50)
            status_text.text(f"✅ Файл загружен. Задача #{task_id} создана")
            
            # Сохраняем ID задачи в сессии
            if 'uploaded_tasks' not in st.session_state:
                st.session_state.uploaded_tasks = []
            
            st.session_state.uploaded_tasks.append({
                'id': task_id,
                'filename': uploaded_file.name,
                'created_at': result.get('created_at'),
                'auto_approve': auto_approve,
                'email_notification': email_notification
            })
            
            progress_bar.progress(100)
            status_text.text("🚀 Обработка началась!")
            
            # Показываем информацию об успехе
            st.success(f"""
            ✅ **Файл успешно загружен и обработка началась!**
            
            **Задача ID:** {task_id}  
            **Файл:** {uploaded_file.name}  
            **Статус:** В обработке  
            
            Вы можете отследить прогресс в разделе "📊 Мои задачи"
            """)
            
            # Кнопка перехода к задачам
            if st.button("📊 Перейти к задачам", type="secondary"):
                st.session_state.page = "📊 Мои задачи"
                st.rerun()
        
        else:
            progress_bar.progress(0)
            status_text.text("❌ Ошибка загрузки")
            st.error("Не удалось загрузить файл. Проверьте подключение к серверу.")
    
    except Exception as e:
        progress_bar.progress(0)
        status_text.text("❌ Ошибка")
        st.error(f"Произошла ошибка при загрузке: {e}")

def show_file_examples():
    """Показывает примеры файлов"""
    
    st.markdown("---")
    st.subheader("📝 Примеры файлов")
    
    # Пример структуры Excel файла
    example_data = {
        'Наименование товара': [
            'Автомобиль легковой Toyota Camry',
            'Кофе натуральный в зернах',
            'Брюки мужские джинсовые',
            'Компьютер ноутбук ASUS'
        ],
        'Количество': [1, 50, 10, 2],
        'Единица измерения': ['шт', 'кг', 'шт', 'шт'],
        'Страна происхождения': ['Япония', 'Бразилия', 'Турция', 'Китай'],
        'Стоимость (USD)': [25000, 500, 300, 800]
    }
    
    example_df = pd.DataFrame(example_data)
    
    st.markdown("**Пример правильной структуры файла:**")
    st.dataframe(example_df, use_container_width=True, hide_index=True)
    
    # Кнопка скачивания примера
    csv_data = example_df.to_csv(index=False, encoding='utf-8-sig')
    
    st.download_button(
        label="📥 Скачать пример CSV",
        data=csv_data,
        file_name="example_products.csv",
        mime="text/csv",
        help="Скачайте этот файл как шаблон для ваших данных"
    ) 