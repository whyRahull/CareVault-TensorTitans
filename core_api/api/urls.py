from django.urls import path, include
from api.views.auth import RegisterView, ProfileView
from api.views.alerts import AlertListView, SOSAlertView, TravelAlertView
from api.views.incidents.general.views import IncidentCreateView, IncidentListView, IncidentDetailView, DashboardStatsView, SeverityCheckView
from api.views.incidents.missing_person.views import (
    MissingPersonListCreateView, MissingPersonDetailView, 
    MarkFoundView, MissingPersonPhotoView
)
from api.views.incidents.hand_sos.views import HandSOSDashboardView, HandSOSImageDetectView
from api.views.incidents.violence.views import ViolenceDashboardView, ViolenceVideoDetectView
from api.views.incidents.lost_child.views import LostChildDashboardView, LostChildImageSearchView

app_name = 'api'

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/profile/', ProfileView.as_view(), name='profile'),
    path('alerts/', AlertListView.as_view(), name='alert-list'),
    path('alerts/sos/', SOSAlertView.as_view(), name='alert-sos'),
    path('alerts/travel/', TravelAlertView.as_view(), name='alert-travel'),
    path('incidents/', IncidentListView.as_view(), name='incident-list'),
    path('incidents/create/', IncidentCreateView.as_view(), name='incident-create'),
    path('incidents/<int:pk>/', IncidentDetailView.as_view(), name='incident-detail'),
    path('incidents/dashboard/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('incidents/check-severity/', SeverityCheckView.as_view(), name='check-severity'),
    path('incidents/missing-persons/', MissingPersonListCreateView.as_view(), name='missing-person-list'),
    path('incidents/missing-persons/<int:pk>/', MissingPersonDetailView.as_view(), name='missing-person-detail'),
    path('incidents/missing-persons/<int:pk>/mark-found/', MarkFoundView.as_view(), name='mark-found'),
    path('incidents/missing-persons/<int:pk>/photo-bytes/', MissingPersonPhotoView.as_view(), name='photo-bytes'),
    path('incidents/hand-sos/detect/', HandSOSImageDetectView.as_view(), name='handsos-detect'),
    path('incidents/violence/detect/', ViolenceVideoDetectView.as_view(), name='violence-detect'),
    path('incidents/lost-child/search/', LostChildImageSearchView.as_view(), name='lostchild-search'),
]
