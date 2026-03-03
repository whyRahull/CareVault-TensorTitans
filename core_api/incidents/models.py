from django.db import models
from django.conf import settings


class Incident(models.Model):
    TYPE_CHOICES = [
        ('violence',  'Violence Detection'),
        ('hand_sos',  'Hand SOS'),
        ('severity',  'Incident Severity'),
        ('lost_child','Lost Child'),
    ]

    incident_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    severity      = models.CharField(max_length=20, blank=True, default='')   # High / Medium / Low
    detected_at   = models.DateTimeField(auto_now_add=True)
    reported_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='incidents',
    )
    camera_room   = models.CharField(max_length=100, blank=True, default='')  # WS room name
    raw_payload   = models.JSONField(default=dict)        # full ML JSON response
    thumbnail_b64 = models.TextField(blank=True, default='')
    is_alerted    = models.BooleanField(default=False)    # email dispatched?

    class Meta:
        ordering = ['-detected_at']

    def __str__(self):
        return f'[{self.incident_type.upper()}] {self.severity} @ {self.detected_at:%Y-%m-%d %H:%M}'
