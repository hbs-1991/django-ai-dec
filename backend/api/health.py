"""
Health Check Views для мониторинга системы
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import redis
import os
from datetime import datetime


class HealthCheckView(APIView):
    """
    Health Check endpoint для проверки состояния системы
    GET /api/health/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Проверка состояния всех компонентов системы"""
        
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': {}
        }
        
        overall_healthy = True
        
        # 1. Проверка базы данных
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            health_status['components']['database'] = {
                'status': 'healthy',
                'details': 'PostgreSQL/SQLite connection OK'
            }
        except Exception as e:
            health_status['components']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            overall_healthy = False
        
        # 2. Проверка Redis (если настроен)
        try:
            redis_url = getattr(settings, 'CELERY_BROKER_URL', None)
            if redis_url and redis_url.startswith('redis://'):
                r = redis.from_url(redis_url)
                r.ping()
                health_status['components']['redis'] = {
                    'status': 'healthy',
                    'details': 'Redis connection OK'
                }
            else:
                health_status['components']['redis'] = {
                    'status': 'not_configured',
                    'details': 'Redis not configured'
                }
        except Exception as e:
            health_status['components']['redis'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            overall_healthy = False
        
        # 3. Проверка Celery worker
        try:
            from celery import current_app
            inspect = current_app.control.inspect()
            stats = inspect.stats()
            
            if stats:
                active_workers = len(stats)
                health_status['components']['celery'] = {
                    'status': 'healthy',
                    'details': f'Active workers: {active_workers}'
                }
            else:
                health_status['components']['celery'] = {
                    'status': 'warning',
                    'details': 'No active Celery workers found'
                }
        except Exception as e:
            health_status['components']['celery'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # 4. Проверка файловой системы
        try:
            media_root = getattr(settings, 'MEDIA_ROOT', '/tmp')
            if os.path.exists(media_root) and os.access(media_root, os.W_OK):
                health_status['components']['filesystem'] = {
                    'status': 'healthy',
                    'details': f'Media directory writable: {media_root}'
                }
            else:
                health_status['components']['filesystem'] = {
                    'status': 'warning',
                    'details': f'Media directory issues: {media_root}'
                }
        except Exception as e:
            health_status['components']['filesystem'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Общий статус
        if not overall_healthy:
            health_status['status'] = 'unhealthy'
            return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        return Response(health_status, status=status.HTTP_200_OK)


class ReadyCheckView(APIView):
    """
    Readiness Check - проверка готовности к обслуживанию запросов
    GET /api/ready/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Проверка готовности системы"""
        
        # Проверяем только критичные компоненты
        try:
            # База данных должна быть доступна
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            return Response({
                'status': 'ready',
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            return Response({
                'status': 'not_ready',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class LivenessCheckView(APIView):
    """
    Liveness Check - проверка жизнеспособности приложения
    GET /api/live/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Простая проверка жизнеспособности"""
        return Response({
            'status': 'alive',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        }) 