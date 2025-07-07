"""
API клиент для взаимодействия с Django backend
"""

import requests
import streamlit as st
from typing import Optional, Dict, Any, List
import os

class APIClient:
    """Клиент для работы с Django REST API"""
    
    def __init__(self, base_url: str = None):
        """
        Инициализация API клиента
        
        Args:
            base_url: Базовый URL API (по умолчанию из настроек)
        """
        self.base_url = base_url or self._get_api_url()
        self.session = requests.Session()
        
        # Настраиваем сессию
        self._setup_session()
    
    def _get_api_url(self) -> str:
        """Получает URL API из настроек или переменных окружения"""
        # Проверяем Streamlit secrets
        if hasattr(st, 'secrets') and 'api' in st.secrets:
            return st.secrets.api.get('base_url', 'http://127.0.0.1:8000/api')
        
        # Проверяем переменные окружения
        return os.getenv('API_BASE_URL', 'http://127.0.0.1:8000/api')
    
    def _setup_session(self):
        """Настройка HTTP сессии"""
        # Базовые заголовки
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })
        
        # Добавляем аутентификацию если есть
        if 'auth_token' in st.session_state:
            self.session.headers['Authorization'] = f"Token {st.session_state.auth_token}"
    
    def get(self, endpoint: str, params: Dict = None) -> Optional[Dict[Any, Any]]:
        """
        GET запрос к API
        
        Args:
            endpoint: Endpoint без базового URL (например '/hs-codes/')
            params: Параметры запроса
            
        Returns:
            JSON ответ или None при ошибке
        """
        try:
            url = f"{self.base_url.rstrip('/')}{endpoint}"
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            st.error(f"Ошибка API запроса: {e}")
            return None
    
    def post(self, endpoint: str, data: Dict = None, files: Dict = None) -> Optional[Dict[Any, Any]]:
        """
        POST запрос к API
        
        Args:
            endpoint: Endpoint без базового URL
            data: Данные для отправки
            files: Файлы для загрузки
            
        Returns:
            JSON ответ или None при ошибке
        """
        try:
            url = f"{self.base_url.rstrip('/')}{endpoint}"
            
            # Если отправляем файлы, не устанавливаем Content-Type
            if files:
                headers = {k: v for k, v in self.session.headers.items() 
                          if k != 'Content-Type'}
                response = requests.post(url, data=data, files=files, headers=headers)
            else:
                response = self.session.post(url, json=data)
            
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            st.error(f"Ошибка API запроса: {e}")
            return None
    
    def patch(self, endpoint: str, data: Dict = None) -> Optional[Dict[Any, Any]]:
        """
        PATCH запрос к API
        
        Args:
            endpoint: Endpoint без базового URL
            data: Данные для обновления
            
        Returns:
            JSON ответ или None при ошибке
        """
        try:
            url = f"{self.base_url.rstrip('/')}{endpoint}"
            response = self.session.patch(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            st.error(f"Ошибка API запроса: {e}")
            return None
    
    def delete(self, endpoint: str) -> bool:
        """
        DELETE запрос к API
        
        Args:
            endpoint: Endpoint без базового URL
            
        Returns:
            True если успешно, False при ошибке
        """
        try:
            url = f"{self.base_url.rstrip('/')}{endpoint}"
            response = self.session.delete(url)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            st.error(f"Ошибка API запроса: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Проверка состояния API
        
        Returns:
            Словарь с информацией о состоянии системы
        """
        try:
            response = self.get('/health/')
            if response:
                return response
        except:
            pass
        
        return {
            'status': 'unhealthy',
            'components': {
                'api': {'status': 'unreachable'}
            }
        }
    
    def search_hs_codes(self, query: str) -> List[Dict]:
        """
        Поиск HS кодов
        
        Args:
            query: Поисковый запрос
            
        Returns:
            Список найденных HS кодов
        """
        response = self.get('/hs-codes/search/', params={'q': query})
        if response:
            return response.get('results', [])
        return []
    
    def get_hs_categories(self) -> List[str]:
        """
        Получение списка категорий HS кодов
        
        Returns:
            Список категорий
        """
        response = self.get('/hs-codes/categories/')
        if response:
            return response.get('categories', [])
        return []
    
    def upload_file(self, file_obj) -> Optional[Dict]:
        """
        Загрузка файла для обработки
        
        Args:
            file_obj: Объект файла Streamlit
            
        Returns:
            Информация о созданной задаче или None
        """
        try:
            files = {'file': (file_obj.name, file_obj.getvalue(), file_obj.type)}
            return self.post('/tasks/', files=files)
        except Exception as e:
            st.error(f"Ошибка загрузки файла: {e}")
            return None
    
    def get_task_status(self, task_id: int) -> Optional[Dict]:
        """
        Получение статуса задачи
        
        Args:
            task_id: ID задачи
            
        Returns:
            Информация о статусе задачи
        """
        return self.get(f'/tasks/{task_id}/status/')
    
    def get_user_tasks(self) -> List[Dict]:
        """
        Получение списка задач пользователя
        
        Returns:
            Список задач
        """
        response = self.get('/tasks/')
        if response:
            return response.get('results', [])
        return [] 