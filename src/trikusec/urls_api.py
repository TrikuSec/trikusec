"""API-only URL configuration"""
from django.urls import path, include
from api.health import health_check

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('api/v1/', include('api.urls', namespace='api_v1')),
    path('api/', include('api.urls_legacy')),
]


