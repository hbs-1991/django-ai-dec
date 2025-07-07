"""
Django команда для тестирования Celery задач
"""

from django.core.management.base import BaseCommand
from processing.tasks import debug_task, mock_classify_product
from core.models import HSCode, ProcessingTask, ProductItem
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Тестирование Celery задач и моделей'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--test-models',
            action='store_true',
            help='Тестировать создание моделей'
        )
        parser.add_argument(
            '--test-celery',
            action='store_true',
            help='Тестировать Celery задачи'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Запуск тестирования AI DECLARANT')
        )
        
        if options['test_models']:
            self.test_models()
        
        if options['test_celery']:
            self.test_celery()
        
        if not any([options['test_models'], options['test_celery']]):
            self.test_models()
            self.test_celery()
    
    def test_models(self):
        """Тестирование моделей"""
        self.stdout.write('\n📊 Тестирование моделей...')
        
        # Создаем тестовые HS коды
        test_codes = [
            {'code': '8703.10.00', 'desc': 'Автомобили легковые', 'category': 'Транспорт'},
            {'code': '6203.42.31', 'desc': 'Брюки мужские из хлопка', 'category': 'Одежда'},
            {'code': '0901.11.00', 'desc': 'Кофе не обжаренный', 'category': 'Продукты'},
        ]
        
        for code_data in test_codes:
            hs_code, created = HSCode.objects.get_or_create(
                code=code_data['code'],
                defaults={
                    'description': code_data['desc'],
                    'category': code_data['category'],
                    'subcategory': 'Общая группа'
                }
            )
            if created:
                self.stdout.write(f'  ✅ Создан HS код: {hs_code.code}')
            else:
                self.stdout.write(f'  ℹ️  HS код уже существует: {hs_code.code}')
        
        # Получаем или создаем пользователя
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'test@example.com', 'first_name': 'Test'}
        )
        if created:
            self.stdout.write(f'  ✅ Создан пользователь: {user.username}')
        
        # Создаем тестовую задачу
        task, created = ProcessingTask.objects.get_or_create(
            user=user,
            file_name='test_file.xlsx',
            defaults={
                'file_path': '/tmp/test_file.xlsx',
                'status': 'pending',
                'total_items': 3
            }
        )
        if created:
            self.stdout.write(f'  ✅ Создана задача: {task.file_name}')
        
        # Создаем тестовые продукты
        test_products = [
            'Автомобиль Toyota Camry 2024',
            'Брюки мужские джинсовые синие',
            'Кофе в зернах арабика Эфиопия'
        ]
        
        for i, product_desc in enumerate(test_products, 1):
            product, created = ProductItem.objects.get_or_create(
                task=task,
                row_number=i,
                defaults={
                    'original_description': product_desc,
                    'quantity': f'{i * 10}',
                    'unit': 'шт'
                }
            )
            if created:
                self.stdout.write(f'  ✅ Создан продукт {i}: {product_desc[:30]}...')
        
        self.stdout.write(
            self.style.SUCCESS(f'📊 Всего HS кодов: {HSCode.objects.count()}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'📋 Всего задач: {ProcessingTask.objects.count()}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'📦 Всего продуктов: {ProductItem.objects.count()}')
        )
    
    def test_celery(self):
        """Тестирование Celery задач"""
        self.stdout.write('\n⚡ Тестирование Celery...')
        
        try:
            # Тестируем функцию классификации
            test_descriptions = [
                'Автомобиль Toyota Camry 2024',
                'Брюки мужские джинсовые',
                'Ноутбук HP Pavilion 15'
            ]
            
            for desc in test_descriptions:
                result = mock_classify_product(desc)
                self.stdout.write(
                    f'  🤖 "{desc[:30]}..." → {result["hs_code"].code} '
                    f'(уверенность: {result["confidence"]:.2f})'
                )
            
            # Пытаемся выполнить задачу через Celery (если доступен)
            try:
                from celery import current_app
                
                # Проверяем, запущен ли Celery worker
                inspect = current_app.control.inspect()
                stats = inspect.stats()
                
                if stats:
                    self.stdout.write('  ✅ Celery worker активен')
                    
                    # Запускаем отладочную задачу
                    result = debug_task.delay()
                    self.stdout.write(f'  🔄 Отладочная задача запущена: {result.id}')
                else:
                    self.stdout.write(
                        self.style.WARNING('  ⚠️  Celery worker не запущен, но функции работают')
                    )
            
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️  Celery недоступен: {e}')
                )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  ❌ Ошибка при тестировании Celery: {e}')
            ) 