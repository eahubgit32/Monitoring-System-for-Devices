# monitoring/serializers.py - FINAL REFACTORED VERSION

import logging
from rest_framework import serializers
from django.contrib.auth.models import User
from django.db.models import Max, F 
from .models import Device, DeviceModel, Metric, UserPreference, Threshold # Import Threshold
from datetime import timedelta               # <--- ADD THIS
from django.utils import timezone
from .models import Device, DeviceModel, Metric, UserPreference, Threshold, Interface

# Get an instance of a logger to print errors to your console
logger = logging.getLogger(__name__)

# --- Serializer 1: UserSerializer ---
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username']

# --- Serializer 2: DeviceModelSerializer ---
class DeviceModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceModel
        fields = ['id', 'model_name']

# --- Serializer 3: DeviceSerializer (The Main One) ---
class DeviceSerializer(serializers.ModelSerializer):
    # READ-ONLY fields (for display)
    model = DeviceModelSerializer(read_only=True)
    user = UserSerializer(read_only=True) 
    
    # WRITE-ONLY field for Model ID (required for POST/PUT)
    model_id = serializers.PrimaryKeyRelatedField(
        queryset=DeviceModel.objects.all(), source='model', write_only=True
    )
    
    # These fields now use database lookup logic
    measurements = serializers.SerializerMethodField(read_only=True)
    status = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Device
        fields = [
            'id', 'name', 'ip_address', 'model', 'user', 
            'status', 'measurements', 'model_id', 'user_id'
        ]
        extra_kwargs = {
            'name': {'source': 'hostname'},
            'ip_address': {'required': False}, 
        }
    
    # --- HELPER FUNCTION 1: Optimized to query all needed metrics at once ---
# --- HELPER FUNCTION 1: Optimized (NOW RETURNS TIMESTAMP) ---
    def get_latest_metrics_data(self, obj):
        
        # 1. Get the pre-fetched history data.
        all_history = obj.history_set.all() 
        if not all_history:
            return {}, None # Return (empty_dict, no_timestamp)

        # 2. Sort by timestamp first to find the most recent one
        #    (We use .all() so we can sort again in Python)
        sorted_by_time = sorted(
            all_history, 
            key=lambda h: h.timestamp, 
            reverse=True
        )
        # This is the newest timestamp for *any* metric
        latest_timestamp = sorted_by_time[0].timestamp 

        # 3. Build the metric dictionary (using the logic from before)
        sorted_by_metric = sorted(
            all_history, 
            key=lambda h: (h.metric_id, h.timestamp), 
            reverse=True
        )
        metrics_dict = {}
        for record in sorted_by_metric:
            # We use .metric_name because the 'metric' object
            # was also pre-fetched by 'history_set__metric'
            metric_name = record.metric.metric_name
            
            if metric_name not in metrics_dict:
                metrics_dict[metric_name] = record.value
        
        # 4. Return BOTH the data and the newest timestamp
        return metrics_dict, latest_timestamp
    
# --- HELPER FUNCTION 2: For Measurements (NOW OPTIMIZED) ---
    def get_measurements(self, obj):
        """
        Fetches real metrics and calculates the status (good, warning, critical)
        for each one based on thresholds.
        """
        # We get the metrics dictionary, but ignore the timestamp
        metrics, _ = self.get_latest_metrics_data(obj)
        
        thresholds = Threshold.objects.filter(device=obj).select_related('metric')

        # Define the order of severity.
        severity_map = { "good": 1, "Warning": 2, "Critical": 3 }

        # Helper to safely convert metric value to a float/int or return 0
        def safe_value(key):
            try:
                # We need to get the value from the 'metrics' dict
                return float(metrics.get(key)) 
            except (TypeError, ValueError):
                return 0 # Returns 0 if key is missing or conversion fails
        
        # --- 1. Get all the raw values first ---
        
        raw_values = {
            "cpu_percent": safe_value('CPU Usage'),           # id: 1
            "memory_used_bytes": safe_value('Memory Used'),   # id: 2
            "memory_free_bytes": safe_value('Memory Free'),   # id: 3
            # "bandwidth_in_mbps" is REMOVED
            # "bandwidth_out_mbps" is REMOVED
            "uptime": metrics.get('System Uptime', "N/A")     # id: 9
        }

        # --- 2. Calculate the status for each metric ---
        
        metric_statuses = {
            "cpu_percent": "good",
            "memory": "good"
            # (Add more as needed)
        }
        
        # List of metrics we can check thresholds for
        NUMERIC_METRIC_NAMES = ['CPU Usage', 'Memory Used', 'Memory Free']

        for t in thresholds:
            metric_name = t.metric.metric_name
            
            if metric_name in metrics and metric_name in NUMERIC_METRIC_NAMES:
                try:
                    cleaned_t_value = t.value.replace('%', '')
                    current_value = float(metrics[metric_name])
                    threshold_value = float(cleaned_t_value)
                except (ValueError, TypeError) as e:
                    logger.warning(f"SKIPPING THRESHOLD: Could not convert {metric_name}: {e}")
                    continue 

                new_alert_level = None
                if t.condition == '>' and current_value > threshold_value:
                    new_alert_level = t.alert_level # "Warning" or "Critical"
                elif t.condition == '<' and current_value < threshold_value:
                    new_alert_level = t.alert_level

                # Update the status if this new alert is more severe
                if new_alert_level:
                    key_to_update = None
                    if metric_name == 'CPU Usage':
                        key_to_update = "cpu_percent"
                    elif metric_name == 'Memory Used' or metric_name == 'Memory Free':
                        key_to_update = "memory"

                    if key_to_update:
                        current_severity = severity_map.get(metric_statuses[key_to_update], 0)
                        new_severity = severity_map.get(new_alert_level, 0)
                        
                        if new_severity > current_severity:
                            # Note: we send the *lowercase* version for CSS
                            metric_statuses[key_to_update] = new_alert_level.lower()

        # --- 3. Build the final JSON response ---
        return {
            "cpu": {
                "value": raw_values["cpu_percent"],
                "status": metric_statuses["cpu_percent"]
            },
            "memory": {
                # We send the raw values
                "used_bytes": raw_values["memory_used_bytes"],
                "free_bytes": raw_values["memory_free_bytes"],
                "status": metric_statuses["memory"]
            },
            # "bandwidth_in_mbps" is REMOVED
            # "bandwidth_out_mbps" is REMOVED
            "uptime": raw_values["uptime"]
        }

    # --- HELPER FUNCTION 3: For Status (NOW SIMPLE) ---
# --- HELPER FUNCTION 3: For Status (NOW WITH HEARTBEAT LOGIC) ---
    def get_status(self, obj):
            """
            Determines status based on whether metrics were *recently* fetched.
            """
            # 1. Get both the metrics and the *newest* timestamp
            metrics, latest_timestamp = self.get_latest_metrics_data(obj)
            
            # 2. If no metrics OR no timestamp, it's definitely down.
            if not metrics or not latest_timestamp:
                return "down"
            
            # 3. Define our "heartbeat" threshold (e.g., 10 minutes)
            #    This is 2x your 5-minute poll interval, which is a safe grace period.
            threshold = timedelta(minutes=10)
            
            # 4. Compare the times
            if timezone.now() - latest_timestamp > threshold:
                # The latest data is *too old*, so the device is down
                return "down"
            
            # 5. If we're here, the data exists AND it's recent.
            return "up"
    
# --- Serializer 4: UserPreferenceSerializer ---
class UserPreferenceSerializer(serializers.ModelSerializer):
    # (This serializer is unchanged)
    user = UserSerializer(read_only=True) 

    class Meta:
        model = UserPreference
        fields = '__all__'
        read_only_fields = ('user',)


# --- Serializer 5: InterfaceSerializer (UPDATED VERSION) ---
class InterfaceSerializer(serializers.ModelSerializer):
    # These are new fields that we will calculate
    bandwidth_in_mb = serializers.SerializerMethodField()
    bandwidth_out_mb = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField() # <-- NEW FIELD

    class Meta:
        model = Interface
        # These fields come directly from the database
        fields = [
            'id', 'ifIndex', 'ifName', 'ifDescr', 'ifAlias', 
            'bandwidth_in_mb', 'bandwidth_out_mb',
            'status' # <-- NEW FIELD
        ]

    def get_latest_metric_value(self, obj, metric_name):
        """
        Helper function to find the newest raw metric value for THIS interface.
        (This finds the data, but does NO conversion)
        """
        try:
            # We look for the metric by name (e.g., "Bandwidth In")
            metric = Metric.objects.get(metric_name=metric_name)
            
            # We search history for this metric *and* this interface_id
            history_record = obj.history_set.filter(
                metric=metric
            ).order_by('-timestamp').first() # Get the newest one

            if history_record:
                return history_record.value
            return None # Return None if no record was found
        except Metric.DoesNotExist:
            return None # Return None if metric name is wrong

    def get_bandwidth_in_mb(self, obj):
        # 1. Get the raw value
        raw_value = self.get_latest_metric_value(obj, "Bandwidth In")
        
        # 2. Do the conversion
        if raw_value:
            try:
                bytes_value = float(raw_value)
                mb_value = bytes_value / (1024 * 1024)
                return round(mb_value, 2)
            except (ValueError, TypeError):
                return 0
        return 0

    def get_bandwidth_out_mb(self, obj):
        # 1. Get the raw value
        raw_value = self.get_latest_metric_value(obj, "Bandwidth Out")
        
        # 2. Do the conversion
        if raw_value:
            try:
                bytes_value = float(raw_value)
                mb_value = bytes_value / (1024 * 1024)
                return round(mb_value, 2)
            except (ValueError, TypeError):
                return 0
        return 0
    
    def get_status(self, obj):
        # 1. Get the raw value for ifOperStatus (from metric table)
        raw_value = self.get_latest_metric_value(obj, "ifOperStatus")
        
        # 2. Clean up the string
        if raw_value:
            # Your history table saves strings like "up(1)" or "down(2)"
            # We can just check if "up" or "down" is in the string.
            if "up" in raw_value.lower():
                return "up"
            if "down" in raw_value.lower():
                return "down"
        
        # Default to "unknown" if no data is found
        return "unknown"