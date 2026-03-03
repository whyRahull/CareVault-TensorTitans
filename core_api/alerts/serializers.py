from rest_framework import serializers
from .models import Alert


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = [
            'id', 'incident', 'recipients', 'subject',
            'body', 'image_filename', 'status', 'sent_at', 'created_at',
        ]
        read_only_fields = ['id', 'status', 'sent_at', 'created_at']


class SOSAlertRequestSerializer(serializers.Serializer):
    """Validates manual SOS trigger from frontend."""
    receiver_emails = serializers.CharField()
    message         = serializers.CharField()
    incident_id     = serializers.IntegerField(required=False, allow_null=True)


class TravelAlertRequestSerializer(serializers.Serializer):
    """Validates manual travel alert trigger."""
    receiver_emails = serializers.CharField()
    vehicle_number  = serializers.CharField()
    vehicle_type    = serializers.CharField()
    vehicle_color   = serializers.CharField()
    driver_name     = serializers.CharField()
    location        = serializers.CharField()
    message         = serializers.CharField(required=False, allow_blank=True, default='')
    incident_id     = serializers.IntegerField(required=False, allow_null=True)
