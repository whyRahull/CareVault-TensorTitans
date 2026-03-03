"""
ASGI config for carevault_core — wires Django Channels WebSocket routing.
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carevault_core.settings')

# Must initialise Django before importing Channels routing
django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from api.websockets.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    'http':      django_asgi_app,
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
