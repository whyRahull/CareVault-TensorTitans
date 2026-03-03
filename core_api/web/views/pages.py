from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import json
from datetime import timedelta
from api.models import Incident


def landing_view(request):
    """Public landing page with project info and MVPs."""
    return render(request, 'web/pages/landing.html')


@login_required
def dashboard_view(request):
    """Logged-in dashboard with navigation tiles."""
    return render(request, 'web/pages/dashboard.html')


@login_required
def analysis_view(request):
    """Incident analysis dashboard with stats and trends."""
    incidents = Incident.objects.all()
    
    # Generate 7-day chart data
    today = timezone.localdate()
    days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    labels = [d.strftime('%a') for d in days]
    
    low_counts = []
    high_counts = []
    
    for d in days:
        day_incidents = incidents.filter(detected_at__date=d)
        low_counts.append(day_incidents.filter(severity__in=['low', 'info']).count())
        high_counts.append(day_incidents.filter(severity__in=['medium', 'high', 'critical']).count())

    chart_data = {
        'labels': labels,
        'low_severity': low_counts,
        'high_severity': high_counts
    }

    context = {
        'total_incidents': incidents.count(),
        'violence_count': incidents.filter(incident_type='violence').count(),
        'sos_count': incidents.filter(incident_type='hand_sos').count(),
        'lost_child_count': incidents.filter(incident_type='lost_child').count(),
        'recent_incidents': incidents.order_by('-detected_at')[:10],
        'chart_data_json': json.dumps(chart_data)
    }
    return render(request, 'web/pages/analysis.html', context)


@login_required
def home_view(request):
    """Legacy/Internal home page."""
    return render(request, 'web/pages/home.html')
