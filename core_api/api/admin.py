from django.contrib import admin
from .models import Organisation, OrgRegistrationToken, MLServiceConfig, MissingPerson, Incident, Alert

@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ('name', 'admin', 'created_at')
    search_fields = ('name', 'admin__username')
    list_filter = ('created_at',)

@admin.register(OrgRegistrationToken)
class OrgRegistrationTokenAdmin(admin.ModelAdmin):
    list_display = ('organisation_name', 'token', 'used', 'expires_at', 'created_by')
    list_filter = ('used', 'expires_at', 'created_by')
    search_fields = ('organisation_name', 'token')
    readonly_fields = ('token',)
    change_list_template = "admin/api/orgregistrationtoken/change_list.html"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('generate-generic-token/', self.admin_site.admin_view(self.generate_token_view), name='generate-generic-token'),
        ]
        return custom_urls + urls

    def generate_token_view(self, request):
        from django.contrib import messages
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        from api.models import OrgRegistrationToken
        from django.utils import timezone
        from datetime import timedelta

        OrgRegistrationToken.objects.create(
            created_by=request.user,
            expires_at=timezone.now() + timedelta(days=3)
        )
        self.message_user(request, "A new generic 3-day token has been generated successfully.")
        return HttpResponseRedirect(reverse('admin:api_orgregistrationtoken_changelist'))

@admin.register(MLServiceConfig)
class MLServiceConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_url', 'is_active', 'timeout_seconds', 'updated_at')
    list_filter = ('is_active',)
    fieldsets = (
        ('Global Configuration', {
            'fields': ('name', 'base_url', 'is_active', 'timeout_seconds')
        }),
        ('API Endpoint Paths', {
            'fields': (
                'health_path', 'violence_path', 'violence_frame_path', 
                'hand_sos_path', 'lost_child_path', 'severity_path'
            ),
            'classes': ('collapse',),
            'description': 'Advanced: Customize the URI paths used to call the ML service endpoints.'
        }),
        ('Feature Capability Toggles', {
            'fields': ('violence_enabled', 'hand_sos_enabled', 'lost_child_enabled', 'severity_enabled', 'sos_enabled')
        }),
    )

@admin.register(MissingPerson)
class MissingPersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'reported_by', 'reported_at', 'is_found')
    list_filter = ('is_found', 'reported_at')
    search_fields = ('name', 'last_seen_location')

@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('incident_type', 'reported_by', 'severity', 'detected_at')
    list_filter = ('incident_type', 'severity', 'detected_at')
    search_fields = ('description', 'camera_room')

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('subject', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('subject', 'recipients')
