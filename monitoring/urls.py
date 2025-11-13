# ... (At the top, import the new view)
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DeviceViewSet, DeviceModelViewSet, login_view, 
    logout_view, UserPreferenceView, DeviceInterfaceListView # Add DeviceInterfaceListView
)
from . import views
from . import api_views

# ... (router setup is unchanged) ...
router = DefaultRouter()
router.register(r'devices', DeviceViewSet, basename='device') 
router.register(r'models', DeviceModelViewSet, basename='devicemodel')


# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
    
    # --- THIS IS THE NEW URL ---
    path('devices/<int:device_id>/interfaces/', DeviceInterfaceListView.as_view(), name='device-interfaces'),
    
    # ... (login/logout/preferences paths are unchanged)
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('preferences/', UserPreferenceView.as_view(), name='user-preferences'),


#====================JOSH==========#
    # This path handles the API request from the React frontend
    path('discover/', views.device_discovery_api, name='device_discovery_api'),
    # Endpoint for frontend metadata
    path('metadata/', api_views.get_device_metadata, name='get_device_metadata'),
    # Endpoint for confirming and registering the device
    path('devices/register/', api_views.confirm_add_device, name='confirm_add_device'),

]