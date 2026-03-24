from django.db import models
from django.conf import settings

class MLServiceConfig(models.Model):
    """Configuration for ML service settings and endpoints."""
    name = models.CharField(max_length=100, default="Primary ML Service")
    base_url = models.CharField(max_length=255, verbose_name="ML Service Base URL", help_text="http://localhost:8001")
    is_active = models.BooleanField(default=True, help_text="Is this the active configuration?")
    
    # Endpoint Paths
    health_path = models.CharField(max_length=100, default="/health")
    violence_path = models.CharField(max_length=100, default="/api/violence/detect")
    violence_frame_path = models.CharField(max_length=100, default="/api/violence/detect_frame")
    hand_sos_path = models.CharField(max_length=100, default="/api/hand_sos/detect")
    lost_child_path = models.CharField(max_length=100, default="/api/lost_child/search")
    severity_path = models.CharField(max_length=100, default="/api/severity/predict")
    
    timeout_seconds = models.PositiveIntegerField(default=10)
    
    # Feature Toggles
    violence_enabled = models.BooleanField(default=True)
    hand_sos_enabled = models.BooleanField(default=True)
    severity_enabled = models.BooleanField(default=True)
    sos_enabled = models.BooleanField(default=True)
    lost_child_enabled = models.BooleanField(default=True)
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ML Service Config"
        verbose_name_plural = "ML Service Configs"
        ordering = ['-is_active', '-updated_at']

    def __str__(self): return f"{self.name} — {self.base_url} ({'ACTIVE' if self.is_active else 'INACTIVE'})"

    def save(self, *args, **kwargs):
        if self.is_active:
            # Rule: only one can be active
            MLServiceConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        """Compatibility method for existing code, returns the active config."""
        return cls.objects.filter(is_active=True).first() or cls.objects.first()

class MissingPerson(models.Model):
    name        = models.CharField(max_length=200)
    age         = models.PositiveIntegerField(null=True, blank=True)
    gender      = models.CharField(max_length=20, blank=True, default='')
    last_seen_location = models.CharField(max_length=255, blank=True, default='')
    description = models.TextField(blank=True, default='')
    photo       = models.ImageField(upload_to='missing_persons/')
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='missing_person_reports')
    reported_at = models.DateTimeField(auto_now_add=True)
    is_found    = models.BooleanField(default=False)
    found_at    = models.DateTimeField(null=True, blank=True)

    class Meta: ordering = ['-reported_at']
    def __str__(self): return f"[{'FOUND' if self.is_found else 'MISSING'}] {self.name}"

class Incident(models.Model):
    TYPE_CHOICES = [('violence', 'Violence Detection'), ('hand_sos', 'Hand SOS'), ('severity', 'Incident Severity'), ('lost_child', 'Lost Child')]
    SEVERITY_CHOICES = [('critical', 'Critical'), ('high', 'High'), ('medium', 'Medium'), ('low', 'Low'), ('info', 'Information')]
    
    incident_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    severity      = models.CharField(max_length=20, choices=SEVERITY_CHOICES, blank=True, default='low')
    detected_at   = models.DateTimeField(auto_now_add=True)
    reported_by   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='incidents')
    camera_room   = models.CharField(max_length=100, blank=True, default='')
    raw_payload   = models.JSONField(default=dict)
    description   = models.TextField(blank=True, default='')
    thumbnail_b64 = models.TextField(blank=True, default='')
    is_alerted    = models.BooleanField(default=False)

    class Meta: ordering = ['-detected_at']
    def __str__(self): return f'[{self.incident_type.upper()}] {self.severity} @ {self.detected_at:%Y-%m-%d %H:%M}'
