from rest_framework import serializers
from api.models.incidents import Incident

class IncidentSerializer(serializers.ModelSerializer):
    reported_by_username = serializers.CharField(
        source='reported_by.username', read_only=True, default=None
    )

    class Meta:
        model = Incident
        fields = [
            'id', 'incident_type', 'severity', 'detected_at',
            'reported_by', 'reported_by_username',
            'camera_room', 'raw_payload', 'thumbnail_b64', 'is_alerted',
        ]
        read_only_fields = ['id', 'detected_at', 'reported_by_username']
