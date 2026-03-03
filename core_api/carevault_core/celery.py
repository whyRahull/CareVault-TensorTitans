"""
Celery application configuration for CareVault Core API.
"""
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carevault_core.settings')

app = Celery('carevault_core')

# Read config from Django settings using CELERY_ namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all INSTALLED_APPS
app.autodiscover_tasks()
