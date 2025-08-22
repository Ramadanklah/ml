"""
Main URL configuration for LIS (Laboratory Information System) project.
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from rest_framework import permissions
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

# API URL patterns
api_v1_patterns = [
    path('auth/', include('users.urls')),
    path('samples/', include('samples.urls')),
    path('tests/', include('tests.urls')),
    path('results/', include('results.urls')),
    path('reports/', include('reports.urls')),
    path('workflows/', include('workflows.urls')),
    path('analytics/', include('analytics.urls')),
]

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API v1
    path('api/v1/', include(api_v1_patterns)),
    
    # Health Checks
    path('health/', include('health_check.urls')),
    
    # Prometheus Metrics
    path('metrics/', include('django_prometheus.urls')),
    
    # Frontend - Catch all routes and serve React app
    re_path(r'^.*$', TemplateView.as_view(template_name='index.html'), name='frontend'),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Customize admin site
admin.site.site_header = "LIS Administration"
admin.site.site_title = "LIS Admin Portal"
admin.site.index_title = "Welcome to LIS Administration"