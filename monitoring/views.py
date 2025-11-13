# monitoring/views.py - FINAL CORRECTED CODE
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.generics import GenericAPIView, ListAPIView # <-- MAKE SURE ListAPIView IS HERE
from .serializers import (
    DeviceSerializer, DeviceModelSerializer, 
    UserPreferenceSerializer, InterfaceSerializer # <-- ADD InterfaceSerializer
)
from monitoring.models import (
    Device, DeviceModel, UserPreference, Interface # <-- ADD Interface
)


#========
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .discover_device import discover_device # Import the function from the new script file


# READ-ONLY VIEWSET (Dropdown Data)
class DeviceModelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DeviceModel.objects.all()
    serializer_class = DeviceModelSerializer
    permission_classes = [AllowAny]


# DEVICE CRUD VIEWSET (The Dashboard/Management)
class DeviceViewSet(viewsets.ModelViewSet):
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated] 

    def perform_create(self, serializer):
        """CRITICAL: Saves the user who created the device."""
        # This line guarantees the device is linked to the logged-in user.
        serializer.save(user=self.request.user)
    
    def get_queryset(self):
        """ Filters the device list based on the user's role. """
        user = self.request.user
        
        if not user.is_authenticated:
            return Device.objects.none()

        # 1. Check for the new query parameter
        # e.g., /api/devices/?include_inactive=true
        #include_inactive = self.request.query_params.get('include_inactive', 'false').lower() == 'true'

        # 2. Define the base query
        base_qs = Device.objects.all() # Start with all devices
        
# 3. Apply filters based on role
        if user.is_superuser:
            # Admin sees all devices
            qs = base_qs.all()
        else:
            # Normal user *always* only sees their own devices.
            qs = base_qs.filter(user_id=user.id)
            
        # --- THIS IS THE NEW, CRITICAL FIX ---
        # This tells Django to fetch all history for all devices in 
        # one or two extra queries, INSTEAD of N queries.
        return qs.prefetch_related(
            'history_set__metric' 
        )
    
    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            return [IsAuthenticated()]
        return super().get_permissions()


# LOGIN VIEW
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
@csrf_exempt
def login_view(request):
    """ Handles user login. """
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(request, username=username, password=password)

    if user is not None:
        login(request, user)
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'role': 'admin' if user.is_staff and user.is_superuser else 'user' 
        }
        return Response(user_data, status=status.HTTP_200_OK)
    else:
        return Response(
            {'detail': 'Invalid username or password.'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )

# LOGOUT VIEW
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """ Handles user logout. """
    logout(request)
    return Response(
        {'detail': 'Successfully logged out.'}, 
        status=status.HTTP_200_OK
    )



# Custom View to handle the single preference object for the current user
class UserPreferenceView(RetrieveModelMixin, UpdateModelMixin, GenericAPIView):
    serializer_class = UserPreferenceSerializer
    permission_classes = [IsAuthenticated]

    # CRITICAL: The queryset is filtered to only include the logged-in user's data
    def get_object(self):
        # We use get_or_create to ensure a preference object exists for the user
        preference, created = UserPreference.objects.get_or_create(user=self.request.user)
        return preference

    # Connects the GET (RetrieveModelMixin) logic to the API endpoint
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    # Connects the PATCH/PUT (UpdateModelMixin) logic to the API endpoint
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
    

# --- NEW VIEW FOR INTERFACES (NEW) ---
class DeviceInterfaceListView(ListAPIView):
    """
    An API view to list all interfaces for a specific device.
    e.g., /api/devices/60/interfaces/
    """
    serializer_class = InterfaceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        This view gets the 'device_id' from the URL and filters
        the Interface table for that device.
        """
        device_id = self.kwargs.get('device_id')
        
        # This is the "Blueprint": Find all interfaces for this device
        return Interface.objects.filter(
            device_id=device_id
        ).prefetch_related( # This makes it fast!
            'history_set__metric'
        ).order_by('ifIndex') # Order by interface number


@csrf_exempt # Allows POST requests from the React frontend without a CSRF token
@require_http_methods(["POST"])
def device_discovery_api(request):
    """
    Receives SNMPv3 credentials and IP, executes the Python discovery script, 
    and returns the JSON result.
    """
    print("Received device discovery request.")
    # 1. Check the request type
    if request.content_type != 'application/json':
        return JsonResponse(
            {"status": "error", "message": "Invalid Content-Type. Must be application/json."}, 
            status=415 # Unsupported Media Type
        )

    try:
        # 2. Parse incoming JSON data
        data = json.loads(request.body.decode('utf-8'))
        
        ip_address = data.get('ipAddress')
        username = data.get('username')
        auth_password = data.get('authPassword')
        priv_password = data.get('privPassword')

        # Basic input validation
        if not all([ip_address, username, auth_password, priv_password]):
            return JsonResponse(
                {"status": "error", "message": "Missing required credentials or IP address."}, 
                status=400
            )

        # 3. Execute the discovery script function
        discovery_results = discover_device(
            username, 
            auth_password, 
            priv_password, 
            ip_address
        )

        # 4. Return results to the frontend
        if discovery_results.get("status") == "error":
            # If the script returned an error, return a server-side error status
            return JsonResponse(discovery_results, status=500)
        
        return JsonResponse(discovery_results, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON format in request body."}, status=400)
    except Exception as e:
        # Catch any unexpected Python errors during script execution
        print(f"Error during device discovery: {e}")
        return JsonResponse({"status": "error", "message": f"Server processing error: {e}"}, status=500)
