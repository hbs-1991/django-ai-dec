"""
Сериализаторы для API endpoints
"""

from rest_framework import serializers
from core.models import HSCode, ProcessingTask, ProductItem
from django.contrib.auth.models import User


class HSCodeSerializer(serializers.ModelSerializer):
    """Сериализатор для HS кодов"""
    
    class Meta:
        model = HSCode
        fields = ['id', 'code', 'description', 'category', 'subcategory', 
                 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class HSCodeSimpleSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для HS кодов (для выпадающих списков)"""
    
    class Meta:
        model = HSCode
        fields = ['id', 'code', 'description']


class ProductItemSerializer(serializers.ModelSerializer):
    """Сериализатор для позиций товаров"""
    
    suggested_hs_code = HSCodeSimpleSerializer(read_only=True)
    final_hs_code = HSCodeSimpleSerializer(read_only=True)
    final_hs_code_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = ProductItem
        fields = ['id', 'row_number', 'original_description', 'quantity', 'unit',
                 'suggested_hs_code', 'confidence_score', 'alternatives', 'ai_reasoning',
                 'status', 'user_comment', 'final_hs_code', 'final_hs_code_id',
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'row_number', 'original_description', 'quantity', 'unit',
                           'suggested_hs_code', 'confidence_score', 'alternatives', 'ai_reasoning',
                           'created_at', 'updated_at']
    
    def update(self, instance, validated_data):
        """Обновление позиции товара (статус, комментарий, финальный код)"""
        final_hs_code_id = validated_data.pop('final_hs_code_id', None)
        
        if final_hs_code_id:
            try:
                final_hs_code = HSCode.objects.get(id=final_hs_code_id)
                instance.final_hs_code = final_hs_code
            except HSCode.DoesNotExist:
                raise serializers.ValidationError({'final_hs_code_id': 'Неверный HS код'})
        
        return super().update(instance, validated_data)


class ProcessingTaskSerializer(serializers.ModelSerializer):
    """Сериализатор для задач обработки"""
    
    user = serializers.StringRelatedField(read_only=True)
    items = ProductItemSerializer(many=True, read_only=True)
    progress_percent = serializers.SerializerMethodField()
    
    class Meta:
        model = ProcessingTask
        fields = ['id', 'user', 'file_name', 'file_path', 'status', 
                 'total_items', 'processed_items', 'progress_percent',
                 'celery_task_id', 'error_message', 'items',
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'status', 'processed_items', 
                           'celery_task_id', 'error_message', 'items',
                           'created_at', 'updated_at']
    
    def get_progress_percent(self, obj):
        """Вычисляет процент выполнения"""
        if obj.total_items > 0:
            return round((obj.processed_items / obj.total_items) * 100, 1)
        return 0.0


class TaskCreateSerializer(serializers.Serializer):
    """Сериализатор для создания новой задачи обработки"""
    
    file = serializers.FileField()
    
    def validate_file(self, value):
        """Валидация загружаемого файла"""
        # Проверяем размер файла (макс 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Файл слишком большой. Максимум 10MB.")
        
        # Проверяем расширение файла
        allowed_extensions = ['.xlsx', '.xls', '.csv']
        if not any(value.name.lower().endswith(ext) for ext in allowed_extensions):
            raise serializers.ValidationError(
                "Неподдерживаемый формат файла. Поддерживаются: Excel (.xlsx, .xls), CSV (.csv)"
            )
        
        return value


class TaskStatusSerializer(serializers.ModelSerializer):
    """Сериализатор для статуса задачи (упрощенный)"""
    
    progress_percent = serializers.SerializerMethodField()
    
    class Meta:
        model = ProcessingTask
        fields = ['id', 'status', 'total_items', 'processed_items', 
                 'progress_percent', 'error_message']
    
    def get_progress_percent(self, obj):
        """Вычисляет процент выполнения"""
        if obj.total_items > 0:
            return round((obj.processed_items / obj.total_items) * 100, 1)
        return 0.0 