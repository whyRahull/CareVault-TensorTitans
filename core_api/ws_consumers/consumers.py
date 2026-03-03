"""
MLStreamConsumer — Django Channels WebSocket consumer.

Flow per frame:
  Browser (WebRTC frame as base64/binary)
    → WS /ws/stream/<room>/
      → Django Channels
        → POST frame to FastAPI ML service
          → receive JSON prediction
            → if detection above threshold → log Incident + trigger alert
              → broadcast result back to WS group (all viewers in room)
"""
import json
import base64
import logging
import httpx

from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

logger = logging.getLogger(__name__)

ML_SERVICE_URL = getattr(settings, 'ML_SERVICE_URL', 'http://localhost:8001')


class MLStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name  = self.scope['url_route']['kwargs']['room_name']
        self.room_group = f'stream_{self.room_name}'

        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()
        logger.info("WS connected: room=%s", self.room_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group, self.channel_name)
        logger.info("WS disconnected: room=%s code=%s", self.room_name, close_code)

    # ------------------------------------------------------------------
    # Receive frame from browser
    # ------------------------------------------------------------------
    async def receive(self, text_data=None, bytes_data=None):
        """
        Accepts two formats from the browser:
        1. Binary bytes   — raw JPEG frame
        2. JSON text      — {type, frame_b64, model}
           type: 'violence' | 'hand_sos' | 'severity'
           frame_b64: base64-encoded JPEG
           model: optional override
        """
        if bytes_data:
            frame_bytes = bytes_data
            model_type  = 'violence'   # default stream model
        else:
            try:
                payload    = json.loads(text_data)
                model_type = payload.get('type', 'violence')
                frame_b64  = payload.get('frame_b64', '')
                frame_bytes = base64.b64decode(frame_b64) if frame_b64 else b''
            except (json.JSONDecodeError, Exception) as e:
                await self.send(json.dumps({'error': f'Invalid payload: {e}'}))
                return

        if not frame_bytes:
            await self.send(json.dumps({'error': 'Empty frame.'}))
            return

        # Route to the correct ML endpoint based on type
        # NOTE: violence uses /detect_frame (single JPEG) not /detect (video file)
        endpoint_map = {
            'violence': f'{ML_SERVICE_URL}/api/violence/detect_frame',
            'hand_sos': f'{ML_SERVICE_URL}/api/hand_sos/detect',
        }
        endpoint = endpoint_map.get(model_type, endpoint_map['violence'])


        ml_response = await self._call_ml_service(endpoint, frame_bytes)

        if ml_response:
            # Broadcast the raw ML result to every client in the group
            await self.channel_layer.group_send(
                self.room_group,
                {
                    'type':    'ml.result',
                    'payload': ml_response,
                    'model':   model_type,
                    'room':    self.room_name,
                }
            )

            # Log incident and potentially trigger alert if detection found
            await self._maybe_log_incident(model_type, ml_response)

    # ------------------------------------------------------------------
    # Group message handler — receives from group_send
    # ------------------------------------------------------------------
    async def ml_result(self, event):
        await self.send(json.dumps({
            'model':   event['model'],
            'room':    event['room'],
            'result':  event['payload'],
        }))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _call_ml_service(self, endpoint: str, frame_bytes: bytes) -> dict | None:
        """POST frame to FastAPI ML service, return JSON or None on error."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    endpoint,
                    files={'file': ('frame.jpg', frame_bytes, 'image/jpeg')},
                )
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            logger.warning("ML service call failed (%s): %s", endpoint, exc)
            await self.send(json.dumps({'error': f'ML service unavailable: {exc}'}))
            return None

    async def _maybe_log_incident(self, model_type: str, ml_result: dict):
        """
        Log an Incident to PostgreSQL if the ML result indicates a detection.
        Runs in the async event loop via database_sync_to_async.
        """
        detected = False
        severity = ''

        if model_type == 'violence' and ml_result.get('suspicious_detected'):
            detected = True
        elif model_type == 'hand_sos' and ml_result.get('sos_detected'):
            detected = True
            severity = 'High'

        if not detected:
            return

        from channels.db import database_sync_to_async
        from incidents.models import Incident
        from alerts.tasks import dispatch_alert
        from alerts.models import Alert

        @database_sync_to_async
        def create_incident_and_alert():
            user = self.scope.get('user')
            auth_user = user if (user and user.is_authenticated) else None

            incident = Incident.objects.create(
                incident_type = model_type,
                severity      = severity,
                camera_room   = self.room_name,
                raw_payload   = ml_result,
                thumbnail_b64 = ml_result.get('thumbnail_b64', '') or ml_result.get('annotated_image_b64', ''),
                reported_by   = auth_user,
            )

            # Auto-create and dispatch alert if user has guardians configured
            recipients = []
            if auth_user:
                recipients = auth_user.get_guardian_email_list()
            if not recipients:
                recipients = getattr(settings, 'DEFAULT_ALERT_RECIPIENTS', [])

            if recipients:
                alert = Alert.objects.create(
                    incident   = incident,
                    recipients = recipients,
                    subject    = f'CareVault Alert: {model_type.replace("_", " ").title()} Detected',
                    body       = f'Detection in camera room "{self.room_name}".\n\nML Result: {ml_result}',
                    status     = 'pending',
                )
                dispatch_alert.delay(alert.pk)

            return incident.pk

        try:
            incident_pk = await create_incident_and_alert()
            logger.info("Logged incident %s (type=%s room=%s)", incident_pk, model_type, self.room_name)
        except Exception as e:
            logger.error("Failed to log incident: %s", e)
