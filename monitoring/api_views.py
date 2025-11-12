from django.shortcuts import get_object_or_404
from django.db import IntegrityError, transaction
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Device, DeviceModel, Interface, Brand, DeviceType
from .serializers import DeviceRegistrationSerializer, BrandSerializer, DeviceTypeSerializer, DeviceModelSimpleSerializer

# @csrf_exempt # Allows POST requests from the React frontend without a CSRF token
@api_view(['GET'])
def get_device_metadata(request):
    """
    API endpoint to fetch all pre-filled data (Brands, Types, Models)
    needed for the frontend dropdowns.
    """
    try:
        brands = Brand.objects.all()
        types = DeviceType.objects.all()
        models = DeviceModel.objects.all()

        data = {
            'brands': BrandSerializer(brands, many=True).data,
            'types': DeviceTypeSerializer(types, many=True).data,
            'models': DeviceModelSimpleSerializer(models, many=True).data,
        }
        return Response(data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"status": "error", "message": f"Could not fetch metadata: {e}"}, 
            status=500
        )

@csrf_exempt # Allows POST requests from the React frontend without a CSRF token
@api_view(['POST'])
def confirm_add_device(request):
    """
    API endpoint to register a new device and its associated interfaces.
    Requires user-selected model_id, device details, and raw discovery data.
    
    This version now uses the actual SNMP ifIndex from the raw_discovery_data.
    """
    print("Received device registration request:", request.data)
    serializer = DeviceRegistrationSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    validated_data = serializer.validated_data
    ip_address = validated_data['ip_address']
    hostname = validated_data['hostname']
    model_id = validated_data['model_id']
    # snmpv3_credentials = validated_data['snmpv3_credentials']
    raw_data = validated_data['raw_discovery_data']

    # --- EXTRACT SNMP CREDENTIALS ---
    # snmp_user = snmpv3_credentials.get('snmp_user', '')
    # auth_pass = snmpv3_credentials.get('auth_pass', '')
    # priv_pass = snmpv3_credentials.get('priv_pass', '')
    snmp_user = raw_data['data']['snmpv3_credentials'].get('snmp_user', '')
    auth_pass = raw_data['data']['snmpv3_credentials'].get('auth_pass', '')
    priv_pass = raw_data['data']['snmpv3_credentials'].get('priv_pass', '')
    
    # --- EXTRACT INTERFACE DATA ---
    # Extract the three lists: indexes, names, and statuses (assuming they are all the same length)
    interface_data = raw_data['data']['interfaces']
    interface_indexes = interface_data.get('indexes', [])
    interface_names = interface_data.get('names', [])
    
    if len(interface_indexes) != len(interface_names):
        return Response({
            'detail': 'Interface data inconsistency: length of indexes does not match length of names.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # --- 1. PRE-CHECKS ---

    # 1.1 Check if IP address already exists
    if Device.objects.filter(ip_address=ip_address).exists():
        return Response({
            'detail': f'A device with IP address {ip_address} already exists.'
        }, status=status.HTTP_409_CONFLICT)

    # 1.2 Get the selected DeviceModel object
    try:
        device_model = get_object_or_404(DeviceModel, pk=model_id)
    except Exception:
         return Response({
            'detail': f'DeviceModel with ID {model_id} not found.'
        }, status=status.HTTP_404_NOT_FOUND)

    # --- 2. ATOMIC TRANSACTION ---
    try:
        with transaction.atomic():
            # 2.1 Create the main Device object
            new_device = Device.objects.create(
                hostname=hostname,
                ip_address=ip_address,
                model=device_model,
                # Assuming the user is authenticated via DRF authentication settings
                user=request.user if request.user.is_authenticated else None,
                # user='admin',  # Placeholder; replace with actual user handling
                username=snmp_user
            )

            # Set and encrypt SNMP passwords
            if auth_pass:
                new_device.set_snmp_password(auth_pass)
            if priv_pass:
                new_device.set_snmp_aes_passwd(priv_pass)
            new_device.save()

            # 2.2 Prepare Interface objects for bulk creation
            interface_objects = []
            
            # Use zip() to pair the index (the SNMP ifIndex) with the name (ifName)
            for snmp_index_str, if_name in zip(interface_indexes, interface_names):
                try:
                    # Convert the SNMP index string to an integer
                    snmp_index = int(snmp_index_str)
                except ValueError:
                    # Handle case where the index is not a valid integer (shouldn't happen with SNMP)
                    print(f"Warning: Invalid SNMP index found: {snmp_index_str}")
                    continue

                interface_objects.append(
                    Interface(
                        device=new_device,
                        # Use the actual SNMP ifIndex retrieved from the device
                        ifIndex=snmp_index, 
                        ifName=if_name,
                        # ifDescr and ifAlias are null/blank by default
                    )
                )

            # 2.3 Bulk create interfaces
            Interface.objects.bulk_create(interface_objects)

        return Response({
            'detail': 'Device and interfaces successfully registered.',
            'device_id': new_device.id,
            'hostname': new_device.hostname
        }, status=status.HTTP_201_CREATED)

    except IntegrityError as e:
        # Catches database errors not caught by the pre-checks (e.g., race condition on IP uniqueness)
        print(f"Database Integrity Error: {e}")
        return Response({
            'detail': 'A database error occurred during registration (e.g., duplicate IP or hostname).',
            'error_message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        # General unexpected errors
        print(f"Unexpected Error: {e}")
        return Response({
            'detail': 'An unexpected error occurred during device registration.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)