import json
import base64
import logging
import httpx
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings

logger = logging.getLogger(__name__)

def _get_ml_config():
    from api.views.incidents.ml_config import get_ml_config
    return get_ml_config()

class MLStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Extract room_name from kwargs, fallback to 'default' or path-based name
        kwargs = self.scope.get('url_route', {}).get('kwargs', {})
        self.room_name = kwargs.get('room_name')
        
        if not self.room_name:
            # Fallback for fixed paths like /ws/ml/stream/handsos/
            path = self.scope.get('path', '')
            if 'hand_sos' in path or 'handsos' in path: self.room_name = 'hand_sos'
            elif 'violence' in path: self.room_name = 'violence'
            elif 'local_cam_' in path: 
                cam_id = kwargs.get('cam_id', 'unknown')
                self.room_name = f'local_cam_{cam_id}'
            else: self.room_name = 'default'

        self.room_group = f'stream_{self.room_name}'
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        person_id = None
        if bytes_data:
            frame_bytes = bytes_data
            model_type  = self.room_name if self.room_name in ['violence', 'hand_sos', 'lost_child'] else 'violence'
        else:
            try:
                payload    = json.loads(text_data)
                # Use payload type if exists, otherwise fallback to room_name
                model_type = payload.get('type')
                if not model_type:
                    model_type = self.room_name if self.room_name in ['violence', 'hand_sos', 'lost_child'] else 'violence'
                
                frame_b64  = payload.get('frame_b64', '')
                frame_bytes = base64.b64decode(frame_b64) if frame_b64 else b''
                person_id  = payload.get('person_id')
            except Exception: return

        @database_sync_to_async
        def get_cfg():
            cfg = _get_ml_config()
            return {'v': cfg.violence_enabled, 'h': cfg.hand_sos_enabled, 'l': cfg.lost_child_enabled, 'url': cfg.base_url, 't': cfg.timeout_seconds}

        cfg = await get_cfg()
        url = cfg['url']
        endpoint_map = {
            'violence': f'{url}/api/violence/detect_frame', 
            'hand_sos': f'{url}/api/hand_sos/detect', 
            'lost_child': f'{url}/api/lost_child/search'
        }
        endpoint = endpoint_map.get(model_type, endpoint_map['violence'])
        if model_type == 'lost_child' and person_id: endpoint = f'{endpoint}?person_id={person_id}'

        ml_response = await self._call_ml_service(endpoint, frame_bytes, cfg['t'])
        if ml_response:
            await self.channel_layer.group_send(self.room_group, {'type': 'ml.result', 'payload': ml_response, 'model': model_type, 'room': self.room_name})
            await self._maybe_log_incident(model_type, ml_response)

    async def ml_result(self, event):
        await self.send(json.dumps({'model': event['model'], 'room': event['room'], 'result': event['payload']}))

    async def _call_ml_service(self, endpoint, frame_bytes, timeout):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(endpoint, files={'file': ('frame.jpg', frame_bytes, 'image/jpeg')})
                return response.json()
        except Exception: return None

    async def _maybe_log_incident(self, model_type, ml_result):
        detected = (model_type == 'violence' and ml_result.get('suspicious_detected')) or \
                   (model_type == 'hand_sos' and ml_result.get('sos_detected')) or \
                   (model_type == 'lost_child' and ml_result.get('matched'))
        if not detected: return

        @database_sync_to_async
        def log_data():
            from api.models.incidents import Incident
            from api.models.alerts import Alert
            from api.tasks import dispatch_alert
            user = self.scope.get('user')
            auth_user = user if (user and user.is_authenticated) else None
            incident = Incident.objects.create(
                incident_type=model_type, camera_room=self.room_name, raw_payload=ml_result,
                thumbnail_b64=ml_result.get('thumbnail_b64', '') or ml_result.get('annotated_image_b64', ''),
                reported_by=auth_user
            )
            recipients = auth_user.get_guardian_email_list() if auth_user else getattr(settings, 'DEFAULT_ALERT_RECIPIENTS', [])
            if recipients:
                alert = Alert.objects.create(incident=incident, recipients=recipients, subject=f"Alert: {model_type}", body=str(ml_result), status='pending')
                dispatch_alert.delay(alert.pk)
        await log_data()
