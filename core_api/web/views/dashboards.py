from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from api.models import MissingPerson, Incident
from api.models import MissingPerson


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_incidents'] = Incident.objects.filter(incident_type='violence').order_by('-detected_at')[:5]
        return context


class HandSOSDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'web/dashboards/dashboard_handsos.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_incidents'] = Incident.objects.filter(incident_type='hand_sos').order_by('-detected_at')[:5]
        return context


class LostChildDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'web/dashboards/dashboard_lostchild.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['missing_persons'] = MissingPerson.objects.filter(is_found=False)
        return context
