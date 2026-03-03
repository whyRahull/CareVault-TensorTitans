from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .forms import OrgRegisterForm, LoginForm, AddEmployeeForm, IncidentReportForm, MissingPersonReportForm, CameraStreamForm
from users.models import CustomUser
from api.models import Organisation, OrgRegistrationToken, Incident, MissingPerson, CameraStream
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .decorators import org_admin_required
import json

def landing_view(request):
    """Public landing page with project info and MVPs."""
    return render(request, 'web/landing.html')

@login_required
def dashboard_view(request):
    """Logged-in dashboard with navigation tiles."""
    return render(request, 'web/dashboard.html')

@login_required
def analysis_view(request):
    """Incident analysis dashboard with stats and trends."""
    # In a real app, this would fetch from the API or local models
    incidents = Incident.objects.all()
    context = {
        'total_incidents': incidents.count(),
        'violence_count': incidents.filter(incident_type='violence').count(),
        'sos_count': incidents.filter(incident_type='hand_sos').count(),
        'lost_child_count': incidents.filter(incident_type='lost_child').count(),
        'recent_incidents': incidents.order_by('-detected_at')[:10]
    }
    return render(request, 'web/analysis.html', context)

def home_view(request):
    """Legacy/Internal home page."""
    return render(request, 'web/home.html')

def login_view(request):
    """Public login page."""
    if request.user.is_authenticated:
        return redirect('web:home')
        
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            # Try username first
            user = authenticate(request, username=username_or_email, password=password)
            if not user:
                # Try email
                try:
                    user_obj = CustomUser.objects.get(email=username_or_email)
                    user = authenticate(request, username=user_obj.username, password=password)
                except CustomUser.DoesNotExist:
                    pass
            
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('web:home')
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    
    return render(request, 'web/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('web:home')

def register_view(request):
    """Org registration using a token."""
    if request.user.is_authenticated:
        return redirect('web:home')
        
    if request.method == 'POST':
        form = OrgRegisterForm(request.POST)
        if form.is_valid():
            token_val = form.cleaned_data['token']
            org_name = form.cleaned_data['org_name']
            admin_name = form.cleaned_data['admin_name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            # Token validation already happened in form.clean_token
            try:
                from django.db import transaction
                token_val = form.cleaned_data['token']
                token_obj = OrgRegistrationToken.objects.get(token=token_val)
                
                if not token_obj.is_valid:
                    messages.error(request, "This token has expired or is already used.")
                    return render(request, 'web/register.html', {'form': form})

                with transaction.atomic():
                    # 1. Create User first (organisation=None is already allowed)
                    user = CustomUser.objects.create_user(
                        username=admin_name,
                        email=email,
                        password=password,
                        role='admin',
                        organisation=None
                    )
                    
                    # 2. Create Organisation with the user as admin (admin is NOT nullable)
                    organisation = Organisation.objects.create(
                        name=org_name,
                        admin=user
                    )
                    
                    # 3. Link user to the created organisation
                    user.organisation = organisation
                    user.save()
                    
                    # 4. Mark token as used
                    token_obj.used = True
                    token_obj.save()
                    
                login(request, user)
                messages.success(request, f"Organisation '{org_name}' registered successfully.")
                return redirect('web:org_panel')
                
            except Exception as e:
                messages.error(request, f"Registration failed: {str(e)}")
    else:
        # Check if URL has ?token=...
        initial = {}
        token_param = request.GET.get('token')
        if token_param:
            try:
                token_obj = OrgRegistrationToken.objects.get(token=token_param, used=False)
                initial['token'] = token_obj.token
                if token_obj.organisation_name:
                    initial['org_name'] = token_obj.organisation_name
            except OrgRegistrationToken.DoesNotExist:
                messages.error(request, "Invalid or expired token link.")
        form = OrgRegisterForm(initial=initial)
        
    return render(request, 'web/register.html', {'form': form})

@org_admin_required
def org_panel_view(request):
    """View employees and org stats."""
    org = request.user.organisation
    employees = org.employees.all()
    context = {
        'organisation': org,
        'employees': employees
    }
    return render(request, 'web/org_panel.html', context)

@org_admin_required
def add_employee_view(request):
    if request.method == 'POST':
        form = AddEmployeeForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.organisation = request.user.organisation
            user.save()
            messages.success(request, f"Employee {user.username} added.")
            return redirect('web:org_panel')
    else:
        form = AddEmployeeForm()
    return render(request, 'web/add_employee.html', {'form': form})

def incidents_view(request):
    """Public list of incidents."""
    incidents = Incident.objects.all().order_by('-detected_at')[:50]
    return render(request, 'web/incidents.html', {'incidents': incidents})

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
    return render(request, 'web/report_incident.html', {'form': form})

def missing_persons_view(request):
    """Public list of missing persons."""
    missing_persons = MissingPerson.objects.all().order_by('-reported_at')
    return render(request, 'web/missing_persons.html', {'missing_persons': missing_persons})

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
    return render(request, 'web/report_missing.html', {'form': form})

@org_admin_required
def camera_manage_view(request):
    org = request.user.organisation
    cameras = org.camera_streams.all()
    if request.method == 'POST':
        form = CameraStreamForm(request.POST)
        if form.is_valid():
            camera = form.save(commit=False)
            camera.organisation = org
            camera.save()
            messages.success(request, f"Camera '{camera.name}' added successfully.")
            return redirect('web:camera_manage')
    else:
        form = CameraStreamForm()
    
    return render(request, 'web/cameras/manage.html', {
        'form': form,
        'cameras': cameras
    })

@org_admin_required
def camera_delete_view(request, pk):
    org = request.user.organisation
    try:
        camera = org.camera_streams.get(pk=pk)
        camera.delete()
        messages.success(request, "Camera deleted.")
    except CameraStream.DoesNotExist:
        messages.error(request, "Camera not found.")
    return redirect('web:camera_manage')

class VigilanceDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'web/dashboards/vigilance.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.organisation:
            context['cameras'] = self.request.user.organisation.camera_streams.filter(is_active=True)
        return context

# Organization Dashboards (ML)
class ViolenceDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'web/dashboards/dashboard_violence.html'

class HandSOSDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'web/dashboards/dashboard_handsos.html'

class LostChildDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'web/dashboards/dashboard_lostchild.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['missing_persons'] = MissingPerson.objects.filter(is_found=False)
        return context
