"""
URL configuration for carevault_core project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({'status': 'ok', 'service': 'CareVault Core API'})


urlpatterns = [
    path('admin/',           admin.site.urls),
    path('',                 include('web.urls', namespace='web')),
    path('api/health/',      health_check,                    name='health'),
    path('api/',             include('api.urls')),
]

# Serve uploaded media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

