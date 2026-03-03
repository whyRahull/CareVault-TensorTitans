from django.urls import path
from .consumers import MLStreamConsumer

websocket_urlpatterns = [
    path("ws/ml/stream/violence/", MLStreamConsumer.as_asgi()),
    path("ws/ml/stream/hand_sos/", MLStreamConsumer.as_asgi()),
    path("ws/ml/stream/local_cam_<int:cam_id>/", MLStreamConsumer.as_asgi()),
    path("ws/stream/<str:room_name>/", MLStreamConsumer.as_asgi()),
]
