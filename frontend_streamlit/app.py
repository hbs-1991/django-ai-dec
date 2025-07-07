"""
AI DECLARANT - Streamlit Frontend
Веб-интерфейс для автоматического определения кодов ТН ВЭД
"""

import streamlit as st
import os
import sys

# Добавляем путь к backend для импорта утилит
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from pages import (
    home,
    upload,
    tasks,
    results,
    hs_codes
)
from utils.auth import require_auth, show_user_info, is_authenticated

# Конфигурация страницы
st.set_page_config(
    page_title="AI DECLARANT",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Главная функция приложения"""
    
    # Заголовок приложения
    st.title("🤖 AI DECLARANT")
    st.markdown("**Автоматическое определение кодов ТН ВЭД для таможенных брокеров**")
    
    # Проверка аутентификации для защищенных страниц
    if not is_authenticated():
        # Показываем только главную страницу без аутентификации
        home.show()
        return
    
    # Боковая панель навигации
    with st.sidebar:
        st.header("📋 Навигация")
        
        # Меню страниц
        page = st.selectbox(
            "Выберите страницу:",
            [
                "🏠 Главная",
                "📤 Загрузка файлов", 
                "📊 Мои задачи",
                "📋 Результаты",
                "🔍 Справочник HS кодов"
            ]
        )
        
        st.markdown("---")
        
        # Информация о системе
        st.subheader("ℹ️ О системе")
        st.markdown("""
        **Версия:** 1.0.0  
        **Статус:** В разработке  
        **Поддержка:** Excel, CSV файлы  
        **Макс. размер:** 10 MB  
        **Макс. позиций:** 1000
        """)
        
        # Быстрые действия
        st.markdown("---")
        st.subheader("⚡ Быстрые действия")
        
        if st.button("🆕 Новая задача", use_container_width=True):
            st.session_state.page = "📤 Загрузка файлов"
            st.rerun()
            
        if st.button("📊 Проверить статус", use_container_width=True):
            st.session_state.page = "📊 Мои задачи"
            st.rerun()
    
    # Показываем информацию о пользователе
    show_user_info()
    
    # Основной контент страницы
    if page == "🏠 Главная":
        home.show()
    elif page == "📤 Загрузка файлов":
        upload.show()
    elif page == "📊 Мои задачи":
        tasks.show()
    elif page == "📋 Результаты":
        results.show()
    elif page == "🔍 Справочник HS кодов":
        hs_codes.show()

if __name__ == "__main__":
    main()
