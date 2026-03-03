from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count
from .models import Incident
from .serializers import IncidentSerializer


class IncidentCreateView(generics.CreateAPIView):
    """
    POST /api/incidents/   — PUBLIC (called by WS consumer or directly from ML service)
    Logs a new ML detection event into PostgreSQL.
    """
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        # Attach authenticated user if present, else leave null
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(reported_by=user)


class IncidentListView(generics.ListAPIView):
    """GET /api/incidents/ — JWT required, paginated, filterable."""
    serializer_class = IncidentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Incident.objects.all()
        incident_type = self.request.query_params.get('type')
        severity      = self.request.query_params.get('severity')
        camera_room   = self.request.query_params.get('room')
        if incident_type:
            qs = qs.filter(incident_type=incident_type)
        if severity:
            qs = qs.filter(severity__iexact=severity)
        if camera_room:
            qs = qs.filter(camera_room=camera_room)
        return qs


class IncidentDetailView(generics.RetrieveAPIView):
    """GET /api/incidents/<id>/ — JWT required."""
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [permissions.IsAuthenticated]


class DashboardStatsView(APIView):
    """
    GET /api/incidents/dashboard/  — JWT required
    Returns aggregate stats and latest incidents per camera room.
    Used by the multi-camera monitoring dashboard.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        total = Incident.objects.count()
        by_type = dict(
            Incident.objects.values_list('incident_type')
                            .annotate(c=Count('id'))
                            .values_list('incident_type', 'c')
        )
        by_severity = dict(
            Incident.objects.exclude(severity='')
                            .values_list('severity')
                            .annotate(c=Count('id'))
                            .values_list('severity', 'c')
        )
        # Latest incident per camera room
        from django.db.models import Max
        room_latest = (
            Incident.objects.values('camera_room')
                            .annotate(last_seen=Max('detected_at'))
                            .order_by('-last_seen')
        )
        # Latest 10 unresolved incidents
        recent = IncidentSerializer(
            Incident.objects.filter(is_alerted=False)[:10],
            many=True,
        ).data

        return Response({
            'total_incidents': total,
            'by_type':         by_type,
            'by_severity':     by_severity,
            'camera_rooms':    list(room_latest),
            'recent_unalerted': recent,
        })
