from django.urls import path
from . import views

app_name = 'web'

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('analysis/', views.analysis_view, name='analysis'),
    path('home/', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('org/', views.org_panel_view, name='org_panel'),
    path('org/add-employee/', views.add_employee_view, name='add_employee'),
    path('incidents/', views.incidents_view, name='incidents'),
    path('incidents/report/', views.report_incident_view, name='report_incident'),
    path('missing-persons/', views.missing_persons_view, name='missing_persons'),
    path('missing-persons/report/', views.report_missing_view, name='report_missing'),
    # ML Dashboards
    path('org/dashboards/violence/', views.ViolenceDashboardView.as_view(), name='dash-violence'),
    path('org/dashboards/hand-sos/', views.HandSOSDashboardView.as_view(), name='dash-handsos'),
    path('org/dashboards/lost-child/', views.LostChildDashboardView.as_view(), name='dash-lostchild'),
    path('org/dashboards/vigilance/', views.VigilanceDashboardView.as_view(), name='dash-vigilance'),
    # Camera Management
    path('org/cameras/', views.camera_manage_view, name='camera_manage'),
    path('org/cameras/delete/<int:pk>/', views.camera_delete_view, name='camera_delete'),
]
