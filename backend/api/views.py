"""
API Views для AI DECLARANT
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django.db.models import Q
import os

from core.models import HSCode, ProcessingTask, ProductItem
from .serializers import (
    HSCodeSerializer, HSCodeSimpleSerializer,
    ProcessingTaskSerializer, ProductItemSerializer,
    TaskCreateSerializer, TaskStatusSerializer
)
from processing.tasks import process_file_task


class HSCodeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для HS кодов
    Только чтение - справочная информация
    """
    queryset = HSCode.objects.filter(is_active=True).order_by('code')
    serializer_class = HSCodeSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_serializer_class(self):
        """Используем упрощенный сериализатор для action search"""
        if self.action == 'search':
            return HSCodeSimpleSerializer
        return super().get_serializer_class()
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Поиск HS кодов по описанию или коду
        GET /api/hs-codes/search/?q=автомобиль
        """
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response({'results': []})
        
        # Поиск по коду или описанию
        queryset = self.get_queryset().filter(
            Q(code__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__icontains=query)
        )[:20]  # Ограничиваем результаты
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({'results': serializer.data})
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """
        Получить список всех категорий
        GET /api/hs-codes/categories/
        """
        categories = HSCode.objects.filter(is_active=True)\
            .values_list('category', flat=True)\
            .distinct()\
            .order_by('category')
        
        return Response({'categories': list(categories)})


class ProcessingTaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet для задач обработки файлов
    """
    serializer_class = ProcessingTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        """Пользователь видит только свои задачи"""
        return ProcessingTask.objects.filter(user=self.request.user)\
            .order_by('-created_at')
    
    def get_serializer_class(self):
        """Разные сериализаторы для разных действий"""
        if self.action == 'create':
            return TaskCreateSerializer
        elif self.action == 'status':
            return TaskStatusSerializer
        return super().get_serializer_class()
    
    def create(self, request, *args, **kwargs):
        """
        Создание новой задачи обработки файла
        POST /api/tasks/ + file
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uploaded_file = serializer.validated_data['file']
        
        # Сохраняем файл
        file_name = uploaded_file.name
        file_path = f'uploads/{request.user.id}/{file_name}'
        saved_path = default_storage.save(file_path, ContentFile(uploaded_file.read()))
        
        # Создаем задачу
        task = ProcessingTask.objects.create(
            user=request.user,
            file_name=file_name,
            file_path=saved_path,
            status='pending'
        )
        
        # Запускаем асинхронную обработку
        celery_task = process_file_task.delay(task.id)
        task.celery_task_id = celery_task.id
        task.save()
        
        # Возвращаем созданную задачу
        task_serializer = ProcessingTaskSerializer(task)
        return Response(task_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """
        Получить статус выполнения задачи
        GET /api/tasks/{id}/status/
        """
        task = self.get_object()
        serializer = self.get_serializer(task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Отменить выполнение задачи
        POST /api/tasks/{id}/cancel/
        """
        task = self.get_object()
        
        if task.status in ['completed', 'failed', 'cancelled']:
            return Response(
                {'error': 'Задача уже завершена или отменена'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Отменяем Celery задачу
        if task.celery_task_id:
            from celery import current_app
            current_app.control.revoke(task.celery_task_id, terminate=True)
        
        task.status = 'cancelled'
        task.save()
        
        return Response({'message': 'Задача отменена'})
    
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """
        Получить позиции товаров для задачи с пагинацией
        GET /api/tasks/{id}/items/?page=1&page_size=50&status=processed
        """
        task = self.get_object()
        
        # Фильтрация по статусу
        items_queryset = task.items.all()
        status_filter = request.query_params.get('status')
        if status_filter:
            items_queryset = items_queryset.filter(status=status_filter)
        
        # Пагинация
        page = self.paginate_queryset(items_queryset)
        if page is not None:
            serializer = ProductItemSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductItemSerializer(items_queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        """
        Экспорт результатов в Excel/CSV
        GET /api/tasks/{id}/export/?format=excel
        """
        task = self.get_object()
        
        if task.status != 'completed':
            return Response(
                {'error': 'Задача еще не завершена'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        export_format = request.query_params.get('format', 'excel')
        
        # TODO: Реализовать экспорт в Excel/CSV
        return Response({
            'message': f'Экспорт в формате {export_format} будет реализован позже',
            'task_id': task.id,
            'total_items': task.total_items
        })


class ProductItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet для позиций товаров
    """
    serializer_class = ProductItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Пользователь видит только позиции своих задач"""
        return ProductItem.objects.filter(task__user=self.request.user)\
            .select_related('task', 'suggested_hs_code', 'final_hs_code')\
            .order_by('task_id', 'row_number')
    
    def update(self, request, *args, **kwargs):
        """
        Обновление позиции товара (статус, комментарий, финальный код)
        PATCH /api/items/{id}/
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Автоматически подтверждаем статус при выборе финального кода
        if 'final_hs_code_id' in serializer.validated_data:
            serializer.validated_data['status'] = 'confirmed'
        
        self.perform_update(serializer)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Подтвердить предложенный HS код
        POST /api/items/{id}/approve/
        """
        item = self.get_object()
        
        if not item.suggested_hs_code:
            return Response(
                {'error': 'Нет предложенного HS кода для подтверждения'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        item.final_hs_code = item.suggested_hs_code
        item.status = 'confirmed'
        item.save()
        
        serializer = self.get_serializer(item)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Отклонить предложенный HS код
        POST /api/items/{id}/reject/
        """
        item = self.get_object()
        
        comment = request.data.get('comment', '')
        item.status = 'needs_review'
        item.user_comment = comment
        item.save()
        
        serializer = self.get_serializer(item)
        return Response(serializer.data)
