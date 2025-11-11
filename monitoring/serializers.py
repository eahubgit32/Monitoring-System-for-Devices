from rest_framework import serializers
from .models import Brand, DeviceType, DeviceModel

class DeviceRegistrationSerializer(serializers.Serializer):
    """
    Serializer to validate the complete payload submitted when confirming a new device.
    This payload combines user-selected metadata (model_id) and raw discovery data.
    """
    # User-provided/confirmed data for the Device table
    ip_address = serializers.IPAddressField(required=True)
    hostname = serializers.CharField(max_length=100, required=True)
    model_id = serializers.IntegerField(required=True, help_text="The ID of the DeviceModel selected by the user.")

    # Raw data output from the device discovery (used to extract interfaces)
    raw_discovery_data = serializers.JSONField(required=True)

    def validate_raw_discovery_data(self, value):
        """
        Ensure the raw data structure contains the necessary interface list.
        """
        try:
            interfaces = value['data']['interfaces']['names']
            if not isinstance(interfaces, list):
                raise serializers.ValidationError("Discovery data interfaces format is invalid.")
        except (KeyError, TypeError):
            raise serializers.ValidationError("Discovery data is missing 'data.interfaces.names' array.")
        return value
    
class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'brand_name']

class DeviceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceType
        fields = ['id', 'type_name']

class DeviceModelSerializer(serializers.ModelSerializer):
    # We use the field names from your models.py
    # 'brand' and 'type' are ForeignKeys, so they will return IDs by default.
    brand = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all(), source='brand.id')
    type = serializers.PrimaryKeyRelatedField(queryset=DeviceType.objects.all(), source='type.id')
    
    # Add a 'display' field for the frontend dropdown
    display = serializers.CharField(source='model_name')

    class Meta:
        model = DeviceModel
        fields = ['id', 'brand', 'type', 'name', 'display']
        # Rename 'brand' and 'type' to match the frontend's expected 'brandId' and 'typeId'
        # This is a bit advanced, let's keep it simple and match the frontend
        
# --- Simplified Serializer to match frontend mock data structure ---
class DeviceModelSimpleSerializer(serializers.ModelSerializer):
    # Use 'source' to rename the fields in the JSON output
    brandId = serializers.IntegerField(source='brand.id')
    typeId = serializers.IntegerField(source='type.id')
    display = serializers.CharField(source='model_name') # Use model_name for display
    name = serializers.CharField(source='model_name') # and for name

    class Meta:
        model = DeviceModel
        fields = ['id', 'brandId', 'typeId', 'name', 'display']