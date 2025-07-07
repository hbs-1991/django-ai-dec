"""
Простая система аутентификации для Streamlit
"""

import streamlit as st
import hashlib
import hmac
from typing import Optional

def hash_password(password: str) -> str:
    """Хеширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Проверка пароля"""
    return hmac.compare_digest(hash_password(password), hashed)

def get_users():
    """Получение списка пользователей (временная реализация)"""
    # В реальном приложении это должно быть из базы данных
    return {
        'admin': {
            'password_hash': hash_password('admin123'),
            'name': 'Администратор',
            'role': 'admin'
        },
        'user': {
            'password_hash': hash_password('user123'),
            'name': 'Пользователь',
            'role': 'user'
        },
        'demo': {
            'password_hash': hash_password('demo'),
            'name': 'Демо пользователь',
            'role': 'demo'
        }
    }

def authenticate(username: str, password: str) -> Optional[dict]:
    """
    Аутентификация пользователя
    
    Args:
        username: Имя пользователя
        password: Пароль
        
    Returns:
        Информация о пользователе или None
    """
    users = get_users()
    
    if username in users:
        user = users[username]
        if verify_password(password, user['password_hash']):
            return {
                'username': username,
                'name': user['name'],
                'role': user['role']
            }
    
    return None

def login(username: str, password: str) -> bool:
    """
    Вход в систему
    
    Args:
        username: Имя пользователя
        password: Пароль
        
    Returns:
        True если успешно, False иначе
    """
    user = authenticate(username, password)
    
    if user:
        st.session_state.authenticated = True
        st.session_state.user = user
        st.success(f"Добро пожаловать, {user['name']}!")
        return True
    else:
        st.error("Неверное имя пользователя или пароль")
        return False

def logout():
    """Выход из системы"""
    st.session_state.authenticated = False
    st.session_state.user = None
    if 'auth_token' in st.session_state:
        del st.session_state.auth_token
    st.success("Вы вышли из системы")

def get_current_user() -> Optional[dict]:
    """
    Получение текущего пользователя
    
    Returns:
        Информация о текущем пользователе или None
    """
    if st.session_state.get('authenticated', False):
        return st.session_state.get('user')
    return None

def is_authenticated() -> bool:
    """Проверка аутентификации"""
    return st.session_state.get('authenticated', False)

def require_auth():
    """Декоратор для страниц, требующих аутентификации"""
    if not is_authenticated():
        show_login_form()
        return False
    return True

def show_login_form():
    """Отображение формы входа"""
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("🔐 Вход в систему")
        
        with st.form("login_form"):
            username = st.text_input("👤 Имя пользователя")
            password = st.text_input("🔑 Пароль", type="password")
            
            col1, col2 = st.columns(2)
            
            with col1:
                login_button = st.form_submit_button("🚀 Войти", use_container_width=True)
            
            with col2:
                demo_button = st.form_submit_button("👀 Демо режим", use_container_width=True)
            
            if login_button and username and password:
                if login(username, password):
                    st.rerun()
            
            elif demo_button:
                if login('demo', 'demo'):
                    st.rerun()
        
        # Подсказки для входа
        with st.expander("💡 Тестовые аккаунты", expanded=False):
            st.markdown("""
            **Для тестирования используйте:**
            
            **Администратор:**
            - Логин: `admin`
            - Пароль: `admin123`
            
            **Пользователь:**
            - Логин: `user`  
            - Пароль: `user123`
            
            **Демо режим:**
            - Логин: `demo`
            - Пароль: `demo`
            """)

def show_user_info():
    """Отображение информации о текущем пользователе"""
    
    user = get_current_user()
    if not user:
        return
    
    with st.sidebar:
        st.markdown("---")
        st.subheader("👤 Пользователь")
        
        # Информация о пользователе
        st.write(f"**Имя:** {user['name']}")
        st.write(f"**Роль:** {user['role']}")
        st.write(f"**Логин:** {user['username']}")
        
        # Кнопка выхода
        if st.button("🚪 Выйти", use_container_width=True):
            logout()
            st.rerun()

def check_permission(required_role: str = None) -> bool:
    """
    Проверка прав доступа
    
    Args:
        required_role: Требуемая роль
        
    Returns:
        True если доступ разрешен
    """
    user = get_current_user()
    
    if not user:
        return False
    
    if not required_role:
        return True
    
    user_role = user.get('role', '')
    
    # Простая система ролей
    role_hierarchy = {
        'admin': ['admin', 'user', 'demo'],
        'user': ['user', 'demo'],
        'demo': ['demo']
    }
    
    allowed_roles = role_hierarchy.get(user_role, [])
    return required_role in allowed_roles

def with_auth(func):
    """
    Декоратор для функций, требующих аутентификации
    
    Args:
        func: Функция для оборачивания
        
    Returns:
        Обернутая функция
    """
    def wrapper(*args, **kwargs):
        if require_auth():
            return func(*args, **kwargs)
        return None
    
    return wrapper 