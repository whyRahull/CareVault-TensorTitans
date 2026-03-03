from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
        ('guardian', 'Guardian'),
    ]

    phone = models.CharField(max_length=20, blank=True, default='')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    organisation = models.ForeignKey(
        'api.Organisation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
        help_text="The organisation this user belongs to. Super-admins have no organisation."
    )
    # Comma-separated guardian emails — receives SOS alerts
    guardian_emails = models.TextField(blank=True, default='')

    def get_guardian_email_list(self):
        """Return guardian_emails as a Python list."""
        return [e.strip() for e in self.guardian_emails.split(',') if e.strip()]

    def __str__(self):
        return f'{self.username} ({self.role})'
