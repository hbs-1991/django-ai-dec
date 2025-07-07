"""
Django команда для тестирования API endpoints
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import HSCode, ProcessingTask, ProductItem
import requests
import json


class Command(BaseCommand):
    help = 'Тестирование API endpoints AI DECLARANT'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--base-url',
            default='http://127.0.0.1:8000',
            help='Базовый URL API'
        )
        parser.add_argument(
            '--test-auth',
            action='store_true',
            help='Тестировать аутентификацию'
        )
    
    def handle(self, *args, **options):
        base_url = options['base_url']
        
        self.stdout.write(
            self.style.SUCCESS('🚀 Тестирование API endpoints AI DECLARANT')
        )
        
        # Тестируем health check
        self.test_health_endpoints(base_url)
        
        # Тестируем HS коды API
        self.test_hs_codes_api(base_url)
        
        if options['test_auth']:
            self.test_authentication(base_url)
    
    def test_health_endpoints(self, base_url):
        """Тестирование health check endpoints"""
        self.stdout.write('\n🔍 Тестирование Health Check endpoints...')
        
        endpoints = [
            '/api/health/',
            '/api/ready/',
            '/api/live/'
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f'{base_url}{endpoint}', timeout=5)
                status_color = self.style.SUCCESS if response.status_code == 200 else self.style.WARNING
                
                self.stdout.write(
                    f'  {status_color(endpoint)} - {response.status_code}'
                )
                
                if endpoint == '/api/health/':
                    data = response.json()
                    self.stdout.write(f'    Статус: {data.get("status")}')
                    
                    # Показываем состояние компонентов
                    for component, status in data.get('components', {}).items():
                        comp_status = status.get('status', 'unknown')
                        color = self.style.SUCCESS if comp_status == 'healthy' else self.style.WARNING
                        self.stdout.write(f'    {color(component)}: {comp_status}')
                
            except requests.RequestException as e:
                self.stdout.write(
                    self.style.ERROR(f'  {endpoint} - ОШИБКА: {e}')
                )
    
    def test_hs_codes_api(self, base_url):
        """Тестирование HS коды API"""
        self.stdout.write('\n📋 Тестирование HS коды API...')
        
        # 1. Список всех HS кодов
        try:
            response = requests.get(f'{base_url}/api/hs-codes/')
            if response.status_code == 200:
                data = response.json()
                count = data.get('count', 0)
                self.stdout.write(
                    self.style.SUCCESS(f'  ✅ Список HS кодов: {count} записей')
                )
                
                # Показываем первые несколько кодов
                for item in data.get('results', [])[:3]:
                    self.stdout.write(f'    {item["code"]} - {item["description"][:50]}...')
            else:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Ошибка получения списка: {response.status_code}')
                )
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Ошибка подключения: {e}'))
        
        # 2. Поиск HS кодов
        search_queries = ['8703', 'автомобиль', 'брюки']
        
        for query in search_queries:
            try:
                response = requests.get(f'{base_url}/api/hs-codes/search/', params={'q': query})
                if response.status_code == 200:
                    data = response.json()
                    results_count = len(data.get('results', []))
                    self.stdout.write(
                        self.style.SUCCESS(f'  🔍 Поиск "{query}": {results_count} результатов')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠️  Поиск "{query}": код {response.status_code}')
                    )
            except requests.RequestException as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Ошибка поиска "{query}": {e}'))
        
        # 3. Категории
        try:
            response = requests.get(f'{base_url}/api/hs-codes/categories/')
            if response.status_code == 200:
                data = response.json()
                categories = data.get('categories', [])
                self.stdout.write(
                    self.style.SUCCESS(f'  📁 Категории: {len(categories)} шт.')
                )
                for category in categories:
                    self.stdout.write(f'    - {category}')
            else:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Ошибка получения категорий: {response.status_code}')
                )
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Ошибка подключения: {e}'))
    
    def test_authentication(self, base_url):
        """Тестирование аутентификации"""
        self.stdout.write('\n🔐 Тестирование аутентификации...')
        
        # Пытаемся получить доступ к защищенному endpoint без аутентификации
        try:
            response = requests.get(f'{base_url}/api/tasks/')
            
            if response.status_code == 401:
                self.stdout.write(
                    self.style.SUCCESS('  ✅ Защита работает: 401 Unauthorized')
                )
            elif response.status_code == 403:
                self.stdout.write(
                    self.style.SUCCESS('  ✅ Защита работает: 403 Forbidden')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️  Неожиданный ответ: {response.status_code}')
                )
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Ошибка подключения: {e}'))
        
        self.stdout.write('\n📊 Статистика базы данных:')
        self.stdout.write(f'  HS кодов: {HSCode.objects.count()}')
        self.stdout.write(f'  Пользователей: {User.objects.count()}')
        self.stdout.write(f'  Задач: {ProcessingTask.objects.count()}')
        self.stdout.write(f'  Позиций товаров: {ProductItem.objects.count()}')
        
        self.stdout.write(
            self.style.SUCCESS('\n✅ Тестирование API завершено!')
        ) 