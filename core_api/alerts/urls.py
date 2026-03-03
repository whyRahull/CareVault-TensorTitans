from django.urls import path
from .views import AlertListView, SOSAlertView, TravelAlertView

urlpatterns = [
    path('',        AlertListView.as_view(),   name='alert-list'),
    path('sos/',    SOSAlertView.as_view(),    name='alert-sos'),
    path('travel/', TravelAlertView.as_view(), name='alert-travel'),
]
