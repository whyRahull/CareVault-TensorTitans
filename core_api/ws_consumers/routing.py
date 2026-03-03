from django.urls import re_path
from .consumers import MLStreamConsumer

websocket_urlpatterns = [
    re_path(r'ws/stream/(?P<room_name>[^/]+)/$', MLStreamConsumer.as_asgi()),
]
