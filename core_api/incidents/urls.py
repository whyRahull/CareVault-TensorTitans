from django.urls import path
from .views import IncidentCreateView, IncidentListView, IncidentDetailView, DashboardStatsView

urlpatterns = [
    path('',            IncidentCreateView.as_view(), name='incident-create'),  # POST (public)
    path('list/',       IncidentListView.as_view(),   name='incident-list'),    # GET (JWT)
    path('<int:pk>/',   IncidentDetailView.as_view(), name='incident-detail'),  # GET (JWT)
    path('dashboard/',  DashboardStatsView.as_view(), name='incident-dashboard'),
]
