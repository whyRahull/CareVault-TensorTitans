import requests
from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models.alerts import Alert
from api.models.incidents import Incident, MLServiceConfig
from api.serializers.incidents.alerts.serializers import AlertSerializer, SOSAlertRequestSerializer, TravelAlertRequestSerializer

class AlertListView(generics.ListAPIView):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]

class SOSAlertView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = SOSAlertRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        email_list = [e.strip() for e in data['receiver_emails'].split(',') if e.strip()]
        if not email_list: return Response({'detail': 'No valid recipient emails.'}, status=400)
        incident_id = data.get('incident_id')
        incident    = Incident.objects.filter(pk=incident_id).first() if incident_id else None
        
        # Call ML service for formatting and validation
        config = MLServiceConfig.get_solo()
        ml_url = f"{config.base_url.rstrip('/')}/api/sos/send"
        try:
            resp = requests.post(
                ml_url, 
                data={'receiver_emails': data['receiver_emails'], 'message': data['message']},
                timeout=config.timeout_seconds
            )
            resp.raise_for_status()
            ml_data = resp.json()
            subject = ml_data.get('subject', 'URGENT SOS Alert')
            body = ml_data.get('body', data['message'])
        except Exception as e:
            # Fallback to local formatting if ML service is down
            subject = 'URGENT SOS Alert'
            body = data['message']

        alert = Alert.objects.create(
            incident=incident, recipients=email_list, 
            subject=subject, body=body, status='pending'
        )
        from api.tasks import dispatch_alert
        dispatch_alert.delay(alert.pk)
        return Response(AlertSerializer(alert).data, status=status.HTTP_202_ACCEPTED)

class TravelAlertView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = TravelAlertRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        email_list = [e.strip() for e in data['receiver_emails'].split(',') if e.strip()]
        if not email_list: return Response({'detail': 'No valid recipient emails.'}, status=400)
        body = f"Emergency Travel Alert\n\nVehicle: {data['vehicle_number']} {data['vehicle_type']} {data['vehicle_color']}\nDriver: {data['driver_name']}\nLocation: {data['location']}\nMsg: {data.get('message')}"
        incident_id = data.get('incident_id')
        incident    = Incident.objects.filter(pk=incident_id).first() if incident_id else None

        # Call ML service for formatting and validation
        config = MLServiceConfig.get_solo()
        ml_url = f"{config.base_url.rstrip('/')}/api/sos/travel"
        try:
            resp = requests.post(
                ml_url, 
                data={
                    'receiver_emails': data['receiver_emails'],
                    'vehicle_number': data['vehicle_number'],
                    'vehicle_type': data['vehicle_type'],
                    'vehicle_color': data['vehicle_color'],
                    'driver_name': data['driver_name'],
                    'location': data['location'],
                    'message': data.get('message', '')
                },
                timeout=config.timeout_seconds
            )
            resp.raise_for_status()
            ml_data = resp.json()
            subject = ml_data.get('subject', 'Emergency Travel Alert')
            body = ml_data.get('body')
        except Exception as e:
            # Fallback to local formatting
            subject = 'Emergency Travel Alert'
            body = f"Emergency Travel Alert\n\nVehicle: {data['vehicle_number']} {data['vehicle_type']} {data['vehicle_color']}\nDriver: {data['driver_name']}\nLocation: {data['location']}\nMsg: {data.get('message')}"

        alert = Alert.objects.create(
            incident=incident, recipients=email_list, 
            subject=subject, body=body, status='pending'
        )
        from api.tasks import dispatch_alert
        dispatch_alert.delay(alert.pk)
        return Response(AlertSerializer(alert).data, status=status.HTTP_202_ACCEPTED)
