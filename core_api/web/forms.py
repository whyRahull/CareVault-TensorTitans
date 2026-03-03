from django import forms
from users.models import CustomUser
from api.models import Organisation, OrgRegistrationToken, Incident, MissingPerson, CameraStream

class TailwindToggleWidget(forms.CheckboxInput):
    template_name = 'web/widgets/tailwind_toggle.html'

class CameraStreamForm(forms.ModelForm):
    class Meta:
        model = CameraStream
        fields = ['name', 'camera_type', 'stream_url', 'is_active']
        widgets = {
            'stream_url': forms.TextInput(attrs={
                'placeholder': 'rtsp://admin:password@192.168.1.100:554/stream1',
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'
            }),
            'is_active': TailwindToggleWidget(attrs={'class': 'sr-only peer'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field not in ['stream_url', 'is_active']:
                self.fields[field].widget.attrs.update({'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'})
from django.contrib.auth import authenticate

class OrgRegisterForm(forms.Form):
    token = forms.UUIDField(label="Registration Token")
    org_name = forms.CharField(max_length=255, label="Organisation Name")
    admin_name = forms.CharField(max_length=255, label="Your Name (Admin)")
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_token(self):
        token = self.cleaned_data.get('token')
        try:
            token_obj = OrgRegistrationToken.objects.get(token=token)
        except OrgRegistrationToken.DoesNotExist:
            raise forms.ValidationError("Invalid token.")
        
        if token_obj.used:
            raise forms.ValidationError("This token has already been used.")
        
        if not token_obj.is_valid:
            raise forms.ValidationError("This token has expired.")
            
        return token

class LoginForm(forms.Form):
    username = forms.CharField(label="Email or Username") # Actually expecting email or username, we'll try both in view
    password = forms.CharField(widget=forms.PasswordInput)

class AddEmployeeForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'role', 'guardian_emails']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Employees cannot be admins by default through this form, usually
        self.fields['role'].choices = [c for c in CustomUser.ROLE_CHOICES if c[0] != 'admin']

class IncidentReportForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = ['incident_type', 'camera_room', 'severity', 'description']

class MissingPersonReportForm(forms.ModelForm):
    class Meta:
        model = MissingPerson
        fields = ['name', 'age', 'gender', 'last_seen_location', 'photo', 'description']
