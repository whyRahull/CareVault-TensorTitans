import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class Organisation(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='managed_organisation'
    )

    def __str__(self):
        return self.name

class OrgRegistrationToken(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    organisation_name = models.CharField(max_length=255, blank=True, null=True, help_text="Optional hint for the organisation name")
    used = models.BooleanField(default=False)
    expires_at = models.DateTimeField(default=None, null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='created_org_tokens'
    )

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=3)
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        return not self.used and self.expires_at > timezone.now()

    def __str__(self):
        return f"{self.organisation_name} - {self.token}"
