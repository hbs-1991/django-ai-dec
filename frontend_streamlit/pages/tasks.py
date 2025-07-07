"""
Страница просмотра задач обработки
"""

import streamlit as st
import pandas as pd
from utils.api_client import APIClient
from datetime import datetime
import time

def show():
    """Отображение страницы задач"""
    
    st.header("📊 Мои задачи обработки")
    st.markdown("Отслеживайте прогресс обработки ваших файлов")
    
    # Кнопки управления
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🔄 Обновить", use_container_width=True):
            st.rerun()
    
    with col2:
        auto_refresh = st.checkbox("⚡ Авто-обновление", value=False)
    
    if auto_refresh:
        # Авто-обновление каждые 5 секунд
        time.sleep(5)
        st.rerun()
    
    # Получение списка задач
    api = APIClient()
    tasks = get_user_tasks(api)
    
    if not tasks:
        show_empty_state()
        return
    
    # Статистика задач
    show_tasks_summary(tasks)
    
    # Фильтры
    st.subheader("🔍 Фильтры")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Статус:",
            options=["Все", "В обработке", "Завершены", "Ошибки", "Отменены"],
            index=0
        )
    
    with col2:
        period_filter = st.selectbox(
            "Период:",
            options=["Все время", "Сегодня", "Неделя", "Месяц"],
            index=0
        )
    
    with col3:
        sort_by = st.selectbox(
            "Сортировка:",
            options=["Дата создания (новые)", "Дата создания (старые)", "Статус", "Имя файла"],
            index=0
        )
    
    # Применение фильтров
    filtered_tasks = apply_filters(tasks, status_filter, period_filter, sort_by)
    
    st.markdown("---")
    
    # Отображение задач
    if filtered_tasks:
        st.subheader(f"📋 Задачи ({len(filtered_tasks)})")
        
        for task in filtered_tasks:
            show_task_card(task, api)
    else:
        st.info("Нет задач, соответствующих выбранным фильтрам")

def get_user_tasks(api: APIClient):
    """Получение задач пользователя"""
    try:
        tasks = api.get_user_tasks()
        
        # Добавляем задачи из локального состояния (если есть)
        if 'uploaded_tasks' in st.session_state:
            local_tasks = st.session_state.uploaded_tasks
            
            # Обновляем статусы локальных задач
            for local_task in local_tasks:
                task_status = api.get_task_status(local_task['id'])
                if task_status:
                    local_task.update(task_status)
            
            # Объединяем списки (избегаем дублирования)
            local_ids = {task['id'] for task in local_tasks}
            for task in tasks:
                if task['id'] not in local_ids:
                    local_tasks.append(task)
            
            return local_tasks
        
        return tasks
    except Exception as e:
        st.error(f"Ошибка при получении задач: {e}")
        return []

def show_tasks_summary(tasks):
    """Отображение сводки по задачам"""
    
    # Подсчет статистики
    total_tasks = len(tasks)
    pending_tasks = len([t for t in tasks if t.get('status') == 'pending'])
    processing_tasks = len([t for t in tasks if t.get('status') == 'processing'])
    completed_tasks = len([t for t in tasks if t.get('status') == 'completed'])
    failed_tasks = len([t for t in tasks if t.get('status') == 'failed'])
    
    # Метрики
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📊 Всего задач", total_tasks)
    
    with col2:
        st.metric("⏳ Ожидают", pending_tasks, help="Задачи в очереди на обработку")
    
    with col3:
        st.metric("🔄 Обрабатываются", processing_tasks, help="Задачи в процессе обработки")
    
    with col4:
        st.metric("✅ Завершены", completed_tasks, help="Успешно обработанные задачи")
    
    with col5:
        st.metric("❌ Ошибки", failed_tasks, help="Задачи с ошибками")

def show_task_card(task, api: APIClient):
    """Отображение карточки задачи"""
    
    # Определяем статус и цвет
    status = task.get('status', 'unknown')
    status_config = get_status_config(status)
    
    with st.container():
        # Заголовок карточки
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"**📄 {task.get('file_name', 'Неизвестный файл')}**")
            st.caption(f"ID: {task.get('id')} • Создано: {format_datetime(task.get('created_at'))}")
        
        with col2:
            st.markdown(f"**{status_config['icon']} {status_config['text']}**")
        
        with col3:
            if status in ['processing', 'pending']:
                if st.button("⏹️ Отменить", key=f"cancel_{task.get('id')}", help="Отменить задачу"):
                    cancel_task(task.get('id'), api)
        
        # Прогресс бар (если есть)
        if status == 'processing':
            progress = task.get('progress_percent', 0) / 100.0
            st.progress(progress)
            
            # Детали прогресса
            total_items = task.get('total_items', 0)
            processed_items = task.get('processed_items', 0)
            
            if total_items > 0:
                st.caption(f"Обработано: {processed_items} из {total_items} позиций ({task.get('progress_percent', 0):.1f}%)")
        
        # Информация о задаче
        if status == 'completed':
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if task.get('total_items'):
                    st.metric("📊 Позиций", task['total_items'])
            
            with col2:
                if st.button("📋 Просмотреть результаты", key=f"view_{task.get('id')}"):
                    st.session_state.selected_task = task.get('id')
                    st.session_state.page = "📋 Результаты"
                    st.rerun()
            
            with col3:
                if st.button("📥 Экспорт", key=f"export_{task.get('id')}"):
                    export_task_results(task.get('id'), api)
        
        elif status == 'failed':
            error_msg = task.get('error_message', 'Неизвестная ошибка')
            st.error(f"Ошибка: {error_msg}")
            
            if st.button("🔄 Повторить", key=f"retry_{task.get('id')}"):
                st.info("Функция повтора будет реализована позже")
        
        st.markdown("---")

def apply_filters(tasks, status_filter, period_filter, sort_by):
    """Применение фильтров к списку задач"""
    
    filtered_tasks = tasks.copy()
    
    # Фильтр по статусу
    if status_filter != "Все":
        status_map = {
            "В обработке": ["pending", "processing"],
            "Завершены": ["completed"],
            "Ошибки": ["failed"],
            "Отменены": ["cancelled"]
        }
        
        allowed_statuses = status_map.get(status_filter, [])
        filtered_tasks = [t for t in filtered_tasks if t.get('status') in allowed_statuses]
    
    # Фильтр по периоду (упрощенная реализация)
    # TODO: Реализовать фильтрацию по дате
    
    # Сортировка
    if sort_by == "Дата создания (новые)":
        filtered_tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    elif sort_by == "Дата создания (старые)":
        filtered_tasks.sort(key=lambda x: x.get('created_at', ''))
    elif sort_by == "Статус":
        filtered_tasks.sort(key=lambda x: x.get('status', ''))
    elif sort_by == "Имя файла":
        filtered_tasks.sort(key=lambda x: x.get('file_name', ''))
    
    return filtered_tasks

def get_status_config(status):
    """Получение конфигурации для статуса"""
    
    config_map = {
        'pending': {'icon': '⏳', 'text': 'Ожидает', 'color': 'orange'},
        'processing': {'icon': '🔄', 'text': 'Обрабатывается', 'color': 'blue'},
        'completed': {'icon': '✅', 'text': 'Завершено', 'color': 'green'},
        'failed': {'icon': '❌', 'text': 'Ошибка', 'color': 'red'},
        'cancelled': {'icon': '⏹️', 'text': 'Отменено', 'color': 'gray'}
    }
    
    return config_map.get(status, {'icon': '❓', 'text': 'Неизвестно', 'color': 'gray'})

def format_datetime(datetime_str):
    """Форматирование даты и времени"""
    if not datetime_str:
        return "Неизвестно"
    
    try:
        # Парсим дату (формат может быть разным)
        if 'T' in datetime_str:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        else:
            dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        
        return dt.strftime('%d.%m.%Y %H:%M')
    except:
        return datetime_str

def cancel_task(task_id, api: APIClient):
    """Отмена задачи"""
    try:
        success = api.post(f'/tasks/{task_id}/cancel/')
        if success:
            st.success("Задача отменена")
            st.rerun()
        else:
            st.error("Не удалось отменить задачу")
    except Exception as e:
        st.error(f"Ошибка при отмене задачи: {e}")

def export_task_results(task_id, api: APIClient):
    """Экспорт результатов задачи"""
    try:
        # TODO: Реализовать экспорт
        st.info("Функция экспорта будет реализована позже")
    except Exception as e:
        st.error(f"Ошибка при экспорте: {e}")

def show_empty_state():
    """Отображение состояния когда нет задач"""
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        ### 📭 У вас пока нет задач
        
        Начните с загрузки файла Excel или CSV с товарами 
        для автоматического определения HS кодов.
        """)
        
        if st.button("📤 Загрузить файл", type="primary", use_container_width=True):
            st.session_state.page = "📤 Загрузка файлов"
            st.rerun()
        
        st.markdown("---")
        
        st.markdown("""
        **💡 Подсказки:**
        - Поддерживаются файлы .xlsx, .xls, .csv
        - Максимальный размер файла: 10 MB
        - Максимальное количество позиций: 1000
        """) 