"""
Админ-интерфейс для основных моделей
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import HSCode, ProcessingTask, ProductItem


@admin.register(HSCode)
class HSCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'description_short', 'category', 'subcategory', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['code', 'description', 'category']
    list_editable = ['is_active']
    ordering = ['code']
    
    def description_short(self, obj):
        """Короткое описание для списка"""
        return obj.description[:100] + "..." if len(obj.description) > 100 else obj.description
    description_short.short_description = "Описание"


class ProductItemInline(admin.TabularInline):
    model = ProductItem
    extra = 0
    readonly_fields = ['row_number', 'original_description', 'suggested_hs_code', 
                      'confidence_score', 'status']
    fields = ['row_number', 'original_description', 'suggested_hs_code', 
             'confidence_score', 'status', 'final_hs_code', 'user_comment']


@admin.register(ProcessingTask)
class ProcessingTaskAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'user', 'status', 'progress_display', 
                   'total_items', 'processed_items', 'created_at']
    list_filter = ['status', 'created_at', 'user']
    search_fields = ['file_name', 'user__username']
    readonly_fields = ['file_path', 'celery_task_id', 'created_at', 'updated_at']
    inlines = [ProductItemInline]
    
    def progress_display(self, obj):
        """Отображение прогресса в админке"""
        percentage = obj.progress_percentage
        color = 'green' if obj.status == 'completed' else 'orange' if obj.status == 'processing' else 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color,
            percentage
        )
    progress_display.short_description = "Прогресс"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(ProductItem)
class ProductItemAdmin(admin.ModelAdmin):
    list_display = ['task_name', 'row_number', 'description_short', 
                   'suggested_hs_code', 'confidence_score', 'status', 'final_hs_code']
    list_filter = ['status', 'task__status', 'confidence_score']
    search_fields = ['original_description', 'suggested_hs_code__code', 'task__file_name']
    readonly_fields = ['task', 'row_number', 'original_description', 
                      'suggested_hs_code', 'confidence_score', 'alternatives', 'ai_reasoning']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('task', 'row_number', 'original_description', 'quantity', 'unit')
        }),
        ('AI классификация', {
            'fields': ('suggested_hs_code', 'confidence_score', 'alternatives', 'ai_reasoning'),
            'classes': ('collapse',)
        }),
        ('Пользовательская проверка', {
            'fields': ('status', 'user_comment', 'final_hs_code')
        }),
    )
    
    def task_name(self, obj):
        """Имя файла задачи"""
        return obj.task.file_name
    task_name.short_description = "Файл"
    
    def description_short(self, obj):
        """Короткое описание товара"""
        return obj.original_description[:50] + "..." if len(obj.original_description) > 50 else obj.original_description
    description_short.short_description = "Описание"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('task', 'suggested_hs_code', 'final_hs_code')


# Настройки админки
admin.site.site_header = "AI DECLARANT Админ Панель"
admin.site.site_title = "AI DECLARANT Admin"
admin.site.index_title = "Управление системой"
