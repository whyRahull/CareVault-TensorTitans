"""
URL configuration for carevault_core project.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({'status': 'ok', 'service': 'CareVault Core API'})


urlpatterns = [
    path('admin/',           admin.site.urls),
    path('api/health/',      health_check,                    name='health'),
    path('api/auth/',        include('users.urls')),
    path('api/incidents/',   include('incidents.urls')),
    path('api/alerts/',      include('alerts.urls')),
]
