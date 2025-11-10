from django.urls import path
from . import views

urlpatterns = [
    # This path handles the API request from the React frontend
    path('discover/', views.device_discovery_api, name='device_discovery_api'),
]