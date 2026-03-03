import logging
from datetime import datetime, timezone
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def dispatch_alert(self, alert_id: int):
    """Send the alert email for the given Alert ID."""
    from api.models.alerts import Alert
    try:
        alert = Alert.objects.get(pk=alert_id)
    except Alert.DoesNotExist:
        logger.error("dispatch_alert: Alert %s not found.", alert_id)
        return

    try:
        send_mail(
            subject=alert.subject,
            message=alert.body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=alert.recipients,
            fail_silently=False,
        )
        alert.status  = 'sent'
        alert.sent_at = datetime.now(timezone.utc)
        alert.save(update_fields=['status', 'sent_at'])
        if alert.incident:
            alert.incident.is_alerted = True
            alert.incident.save(update_fields=['is_alerted'])
    except Exception as exc:
        alert.status = 'failed'
        alert.save(update_fields=['status'])
        raise self.retry(exc=exc)
