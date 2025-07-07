"""
Основные модели данных для AI DECLARANT
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class TimestampedModel(models.Model):
    """Абстрактная модель с временными метками"""
    created_at = models.DateTimeField(_("Создано"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)
    
    class Meta:
        abstract = True


class HSCode(TimestampedModel):
    """Модель HS кода (код ТН ВЭД)"""
    code = models.CharField(_("HS код"), max_length=10, unique=True)
    description = models.TextField(_("Описание"))
    category = models.CharField(_("Категория"), max_length=100)
    subcategory = models.CharField(_("Подкатегория"), max_length=100, blank=True)
    is_active = models.BooleanField(_("Активен"), default=True)
    
    class Meta:
        verbose_name = _("HS код")
        verbose_name_plural = _("HS коды")
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.description[:50]}"


class ProcessingTask(TimestampedModel):
    """Модель задачи обработки файла"""
    
    STATUS_CHOICES = [
        ('pending', _('Ожидание')),
        ('processing', _('Обработка')),
        ('completed', _('Завершено')),
        ('failed', _('Ошибка')),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("Пользователь"))
    file_name = models.CharField(_("Имя файла"), max_length=255)
    file_path = models.CharField(_("Путь к файлу"), max_length=500)
    status = models.CharField(_("Статус"), max_length=20, choices=STATUS_CHOICES, default='pending')
    total_items = models.PositiveIntegerField(_("Всего позиций"), default=0)
    processed_items = models.PositiveIntegerField(_("Обработано позиций"), default=0)
    celery_task_id = models.CharField(_("ID задачи Celery"), max_length=255, null=True, blank=True)
    error_message = models.TextField(_("Сообщение об ошибке"), blank=True)
    
    class Meta:
        verbose_name = _("Задача обработки")
        verbose_name_plural = _("Задачи обработки")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.file_name} - {self.get_status_display()}"
    
    @property
    def progress_percentage(self):
        """Процент выполнения"""
        if self.total_items == 0:
            return 0
        return round((self.processed_items / self.total_items) * 100, 2)


class ProductItem(TimestampedModel):
    """Модель позиции товара для классификации"""
    
    ITEM_STATUS_CHOICES = [
        ('pending', _('Ожидание')),
        ('processed', _('Обработано')),
        ('confirmed', _('Подтверждено')),
        ('needs_review', _('Требует проверки')),
        ('rejected', _('Отклонено')),
    ]
    
    task = models.ForeignKey(ProcessingTask, on_delete=models.CASCADE, 
                           related_name='items', verbose_name=_("Задача"))
    row_number = models.PositiveIntegerField(_("Номер строки"))
    original_description = models.TextField(_("Исходное описание"))
    quantity = models.CharField(_("Количество"), max_length=100, blank=True)
    unit = models.CharField(_("Единица измерения"), max_length=50, blank=True)
    
    # AI классификация
    suggested_hs_code = models.ForeignKey(HSCode, on_delete=models.SET_NULL, 
                                        null=True, blank=True, 
                                        verbose_name=_("Предложенный HS код"))
    confidence_score = models.FloatField(_("Уровень доверия"), default=0.0)
    alternatives = models.JSONField(_("Альтернативные коды"), default=list)
    ai_reasoning = models.TextField(_("Обоснование AI"), blank=True)
    
    # Пользовательская проверка
    status = models.CharField(_("Статус"), max_length=20, 
                            choices=ITEM_STATUS_CHOICES, default='pending')
    user_comment = models.TextField(_("Комментарий пользователя"), blank=True)
    final_hs_code = models.ForeignKey(HSCode, on_delete=models.SET_NULL, 
                                    null=True, blank=True, 
                                    related_name='final_items',
                                    verbose_name=_("Финальный HS код"))
    
    class Meta:
        verbose_name = _("Позиция товара")
        verbose_name_plural = _("Позиции товаров")
        ordering = ['task', 'row_number']
        unique_together = ['task', 'row_number']
    
    def __str__(self):
        return f"Строка {self.row_number}: {self.original_description[:30]}"
    
    @property
    def display_hs_code(self):
        """Отображаемый HS код (финальный или предложенный)"""
        return self.final_hs_code or self.suggested_hs_code
