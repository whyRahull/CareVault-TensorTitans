from django.db import models
from incidents.models import Incident


class Alert(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent',    'Sent'),
        ('failed',  'Failed'),
    ]

    incident      = models.OneToOneField(
        Incident, on_delete=models.CASCADE,
        related_name='alert', null=True, blank=True,
    )
    recipients    = models.JSONField(default=list)   # list of email strings
    subject       = models.CharField(max_length=255)
    body          = models.TextField()
    image_filename= models.CharField(max_length=255, blank=True, default='')
    status        = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    sent_at       = models.DateTimeField(null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Alert [{self.status}] → {self.recipients}'
