from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    # This path handles the API request from the React frontend
    path('discover/', views.device_discovery_api, name='device_discovery_api'),
    # Endpoint for frontend metadata
    path('metadata/', api_views.get_device_metadata, name='get_device_metadata'),
    # Endpoint for confirming and registering the device
    path('devices/register/', api_views.confirm_add_device, name='confirm_add_device'),
]