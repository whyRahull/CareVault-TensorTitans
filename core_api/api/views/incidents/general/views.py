from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Max
import requests
from api.models.incidents import Incident, MLServiceConfig
from api.serializers.incidents.general.serializers import IncidentSerializer

class IncidentCreateView(generics.CreateAPIView):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(reported_by=user)

class IncidentListView(generics.ListAPIView):
    serializer_class = IncidentSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Incident.objects.all()
        incident_type = self.request.query_params.get('type')
        severity      = self.request.query_params.get('severity')
        camera_room   = self.request.query_params.get('room')
        if incident_type: qs = qs.filter(incident_type=incident_type)
        if severity: qs = qs.filter(severity__iexact=severity)
        if camera_room: qs = qs.filter(camera_room=camera_room)
        return qs

class IncidentDetailView(generics.RetrieveAPIView):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [permissions.IsAuthenticated]

class DashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        total = Incident.objects.count()
        by_type = dict(Incident.objects.values_list('incident_type').annotate(c=Count('id')).values_list('incident_type', 'c'))
        by_severity = dict(Incident.objects.exclude(severity='').values_list('severity').annotate(c=Count('id')).values_list('severity', 'c'))
        room_latest = Incident.objects.values('camera_room').annotate(last_seen=Max('detected_at')).order_by('-last_seen')
        recent = IncidentSerializer(Incident.objects.filter(is_alerted=False)[:10], many=True).data
        return Response({'total_incidents': total, 'by_type': by_type, 'by_severity': by_severity, 'camera_rooms': list(room_latest), 'recent_unalerted': recent})

class SeverityCheckView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        description = request.data.get('description')
        if not description:
            return Response({'error': 'Description is required'}, status=400)

        config = MLServiceConfig.get_solo()
        ml_url = f"{config.base_url.rstrip('/')}{config.severity_path}"
        
        try:
            resp = requests.post(
                ml_url, 
                json={'description': description},
                timeout=config.timeout_seconds
            )
            resp.raise_for_status()
            return Response(resp.json())
        except Exception as e:
            return Response({'error': f"ML Service error: {str(e)}"}, status=503)
