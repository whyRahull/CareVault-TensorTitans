from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Alert
from .serializers import AlertSerializer, SOSAlertRequestSerializer, TravelAlertRequestSerializer
from .tasks import dispatch_alert


class AlertListView(generics.ListAPIView):
    """GET /api/alerts/  — JWT required, returns alert history."""
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]


class SOSAlertView(APIView):
    """POST /api/alerts/sos/ — JWT required. Triggers immediate SOS email via Celery."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SOSAlertRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        email_list = [e.strip() for e in data['receiver_emails'].split(',') if e.strip()]
        if not email_list:
            return Response({'detail': 'No valid recipient emails.'}, status=400)

        incident_id = data.get('incident_id')
        incident    = None
        if incident_id:
            from incidents.models import Incident
            incident = Incident.objects.filter(pk=incident_id).first()

        alert = Alert.objects.create(
            incident      = incident,
            recipients    = email_list,
            subject       = 'URGENT: Emergency Assistance Needed! — CareVault',
            body          = data['message'],
            status        = 'pending',
        )

        # Dispatch async via Celery
        dispatch_alert.delay(alert.pk)

        return Response(AlertSerializer(alert).data, status=status.HTTP_202_ACCEPTED)


class TravelAlertView(APIView):
    """POST /api/alerts/travel/ — JWT required. Sends a travel-details alert via Celery."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = TravelAlertRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        email_list = [e.strip() for e in data['receiver_emails'].split(',') if e.strip()]
        if not email_list:
            return Response({'detail': 'No valid recipient emails.'}, status=400)

        body = (
            f"🚨 Emergency Alert from CareVault SOS Hub\n\n"
            f"Vehicle Details:\n"
            f"  Number : {data['vehicle_number']}\n"
            f"  Type   : {data['vehicle_type']}\n"
            f"  Color  : {data['vehicle_color']}\n\n"
            f"Driver  : {data['driver_name']}\n"
            f"Location: {data['location']}\n\n"
            f"Message : {data.get('message') or 'No additional information.'}"
        )

        incident_id = data.get('incident_id')
        incident    = None
        if incident_id:
            from incidents.models import Incident
            incident = Incident.objects.filter(pk=incident_id).first()

        alert = Alert.objects.create(
            incident   = incident,
            recipients = email_list,
            subject    = 'CareVault Emergency Travel Alert',
            body       = body,
            status     = 'pending',
        )

        dispatch_alert.delay(alert.pk)

        return Response(AlertSerializer(alert).data, status=status.HTTP_202_ACCEPTED)
