from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from ..forms import IncidentReportForm, MissingPersonReportForm
from api.models import Incident, MissingPerson


def incidents_view(request):
    """Public list of incidents with filtering and pagination."""
    queryset = Incident.objects.all().order_by('-detected_at')
    
    # Filtering
    incident_type = request.GET.get('type')
    if incident_type:
        queryset = queryset.filter(incident_type=incident_type)
        
    severity = request.GET.get('severity')
    if severity:
        queryset = queryset.filter(severity=severity)

    # Pagination
    paginator = Paginator(queryset, 20) # 20 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'current_type': incident_type,
        'current_severity': severity
    }
    return render(request, 'web/incidents/incidents.html', context)


def report_incident_view(request):
    """Public page to report an incident manually."""
    if request.method == 'POST':
        form = IncidentReportForm(request.POST)
        if form.is_valid():
            incident = form.save(commit=False)
            if request.user.is_authenticated:
                incident.reported_by = request.user
            incident.save()
            messages.success(request, "Incident reported successfully.")
            return redirect('web:incidents')
    else:
        form = IncidentReportForm()
    return render(request, 'web/incidents/report_incident.html', {'form': form})


def missing_persons_view(request):
    """Public list of missing persons."""
    missing_persons = MissingPerson.objects.all().order_by('-reported_at')
    return render(request, 'web/incidents/missing_persons.html', {'missing_persons': missing_persons})


def report_missing_view(request):
    """Public page to report a missing person."""
    if request.method == 'POST':
        form = MissingPersonReportForm(request.POST, request.FILES)
        if form.is_valid():
            person = form.save(commit=False)
            if request.user.is_authenticated:
                person.reported_by = request.user
            person.save()
            messages.success(request, "Missing person report submitted.")
            return redirect('web:missing_persons')
    else:
        form = MissingPersonReportForm()
    return render(request, 'web/incidents/report_missing.html', {'form': form})
