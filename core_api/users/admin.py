from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Fieldsets for editing
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('phone', 'role', 'organisation', 'guardian_emails')}),
    )
    # Fieldsets for creation
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('phone', 'role', 'organisation', 'guardian_emails')}),
    )
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'organisation', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'organisation')
    search_fields = ('username', 'first_name', 'last_name', 'email')
