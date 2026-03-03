from django.db import models
from .organisations import Organisation

class CameraStream(models.Model):
    CAMERA_TYPES = [
        ('LOCAL', 'Laptop Camera'),
        ('REMOTE', 'Remote Stream (RTSP/HTTP)'),
    ]

    name = models.CharField(max_length=255)
    camera_type = models.CharField(max_length=10, choices=CAMERA_TYPES, default='LOCAL')
    stream_url = models.CharField(max_length=1024, blank=True, null=True, help_text="RTSP or HTTP URL for remote streams")
    is_active = models.BooleanField(default=True)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='camera_streams')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_camera_type_display()})"

    class Meta:
        ordering = ['name']
