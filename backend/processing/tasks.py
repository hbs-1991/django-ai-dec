"""
Celery задачи для обработки файлов
"""

from celery import shared_task
from django.core.mail import mail_admins
from core.models import ProcessingTask, ProductItem, HSCode
import pandas as pd
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def debug_task(self):
    """Отладочная задача"""
    print(f'Request: {self.request!r}')
    return 'Debug task completed'


@shared_task(bind=True)
def process_file_task(self, task_id):
    """
    Основная задача обработки файла
    """
    try:
        # Получаем задачу из БД
        task = ProcessingTask.objects.get(id=task_id)
        task.status = 'processing'
        task.celery_task_id = self.request.id
        task.save()
        
        # Обновляем прогресс
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Начинаем обработку...'}
        )
        
        # Читаем файл
        logger.info(f"Начинаем обработку файла: {task.file_name}")
        df = pd.read_excel(task.file_path) if task.file_path.endswith('.xlsx') else pd.read_csv(task.file_path)
        
        total_rows = len(df)
        task.total_items = total_rows
        task.save()
        
        # Обрабатываем каждую строку
        for index, row in df.iterrows():
            # Создаем ProductItem
            product_item = ProductItem.objects.create(
                task=task,
                row_number=index + 1,
                original_description=str(row.get('description', '')),
                quantity=str(row.get('quantity', '')),
                unit=str(row.get('unit', ''))
            )
            
            # Симуляция AI классификации (заглушка)
            # TODO: Здесь будет реальная AI обработка
            mock_classification_result = mock_classify_product(product_item.original_description)
            
            # Обновляем результат
            product_item.suggested_hs_code = mock_classification_result['hs_code']
            product_item.confidence_score = mock_classification_result['confidence']
            product_item.ai_reasoning = mock_classification_result['reasoning']
            product_item.alternatives = mock_classification_result['alternatives']
            product_item.status = 'processed'
            product_item.save()
            
            # Обновляем прогресс
            processed = index + 1
            task.processed_items = processed
            task.save()
            
            # Обновляем состояние задачи
            progress_percent = int((processed / total_rows) * 100)
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': processed,
                    'total': total_rows,
                    'percent': progress_percent,
                    'status': f'Обработано {processed} из {total_rows} позиций'
                }
            )
        
        # Завершаем задачу
        task.status = 'completed'
        task.save()
        
        logger.info(f"Обработка файла {task.file_name} завершена успешно")
        
        return {
            'status': 'completed',
            'total_items': total_rows,
            'processed_items': total_rows,
            'message': f'Файл {task.file_name} обработан успешно'
        }
        
    except Exception as exc:
        logger.error(f"Ошибка при обработке файла: {exc}")
        
        # Обновляем статус задачи
        task.status = 'failed'
        task.error_message = str(exc)
        task.save()
        
        # Уведомляем админов
        mail_admins(
            'Ошибка обработки файла',
            f'Ошибка при обработке файла {task.file_name}: {exc}'
        )
        
        # Перебрасываем исключение
        raise self.retry(exc=exc, countdown=60, max_retries=3)


def mock_classify_product(description):
    """
    Временная заглушка для AI классификации
    TODO: Заменить на реальный AI агент
    """
    import random
    
    # Простая логика на основе ключевых слов
    description_lower = description.lower()
    
    mock_codes = [
        {'code': '8703.10.00', 'desc': 'Автомобили легковые'},
        {'code': '6203.42.31', 'desc': 'Брюки мужские из хлопка'},
        {'code': '0901.11.00', 'desc': 'Кофе не обжаренный'},
        {'code': '8471.30.00', 'desc': 'Машины вычислительные портативные'},
        {'code': '6204.62.31', 'desc': 'Брюки женские из хлопка'},
    ]
    
    # Выбираем подходящий код (очень примитивная логика)
    if any(word in description_lower for word in ['автомобиль', 'машина', 'авто']):
        selected_code = mock_codes[0]
        confidence = 0.85
    elif any(word in description_lower for word in ['брюки', 'штаны']):
        selected_code = mock_codes[1] if 'мужск' in description_lower else mock_codes[4]
        confidence = 0.75
    elif any(word in description_lower for word in ['кофе', 'coffee']):
        selected_code = mock_codes[2]
        confidence = 0.90
    elif any(word in description_lower for word in ['компьютер', 'ноутбук', 'laptop']):
        selected_code = mock_codes[3]
        confidence = 0.80
    else:
        selected_code = random.choice(mock_codes)
        confidence = random.uniform(0.3, 0.7)
    
    # Создаем или получаем HS код
    hs_code, created = HSCode.objects.get_or_create(
        code=selected_code['code'],
        defaults={
            'description': selected_code['desc'],
            'category': 'Товары народного потребления',
            'subcategory': 'Общая группа'
        }
    )
    
    return {
        'hs_code': hs_code,
        'confidence': confidence,
        'reasoning': f'Классификация на основе ключевых слов в описании: "{description[:50]}..."',
        'alternatives': [
            {'code': code['code'], 'confidence': random.uniform(0.2, 0.6)} 
            for code in random.sample(mock_codes, 2)
        ]
    }


@shared_task
def cleanup_old_tasks():
    """Очистка старых задач (запускается по расписанию)"""
    from datetime import datetime, timedelta
    
    # Удаляем задачи старше 30 дней
    cutoff_date = datetime.now() - timedelta(days=30)
    old_tasks = ProcessingTask.objects.filter(
        created_at__lt=cutoff_date,
        status__in=['completed', 'failed']
    )
    
    count = old_tasks.count()
    old_tasks.delete()
    
    logger.info(f"Удалено {count} старых задач")
    return f"Удалено {count} старых задач"


@shared_task
def send_daily_report():
    """Отправка ежедневного отчета"""
    from django.contrib.auth.models import User
    from django.utils import timezone
    
    today = timezone.now().date()
    
    # Статистика за сегодня
    tasks_today = ProcessingTask.objects.filter(created_at__date=today)
    completed_today = tasks_today.filter(status='completed').count()
    failed_today = tasks_today.filter(status='failed').count()
    
    # Формируем отчет
    report = f"""
    Ежедневный отчет AI DECLARANT за {today}
    
    Задач создано: {tasks_today.count()}
    Успешно завершено: {completed_today}
    Завершено с ошибкой: {failed_today}
    
    Активных пользователей: {User.objects.filter(last_login__date=today).count()}
    """
    
    mail_admins('Ежедневный отчет AI DECLARANT', report)
    return "Отчет отправлен" 