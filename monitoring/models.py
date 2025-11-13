from django.db import models
from django.contrib.auth.models import User
from cryptography.fernet import Fernet
from django.conf import settings

# Uses Django's built-in User model to represent system users
# (e.g., admins, operators, or whoever owns/manages a device).

# ======================
# BRAND TABLE
# ======================
class Brand(models.Model):
    # Stores the name of a device brand (e.g., Cisco, Juniper, Huawei)
    brand_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        # Makes it display the brand name in the Django admin or shell
        return self.brand_name


# ======================
# DEVICE TYPE TABLE
# ======================
class DeviceType(models.Model):
    # Stores the type/category of a device (e.g., Router, Switch, Server)
    type_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.type_name


# ======================
# METRIC TABLE
# ======================
class Metric(models.Model):
    # Represents measurable parameters (e.g., CPU Usage, Memory, Bandwidth)
    metric_name = models.CharField(max_length=100, unique=True)

    # Unit of measurement (e.g., %, MB, Mbps)
    unit = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.metric_name


# ======================
# DEVICE MODEL TABLE
# ======================
class DeviceModel(models.Model):
    # The specific model name (e.g., Cisco 2960, Juniper EX2200)
    model_name = models.CharField(max_length=100)

    # A brand can have many models; deleting a brand is restricted if models exist
    brand = models.ForeignKey(Brand, on_delete=models.RESTRICT)

    # The model belongs to a type (e.g., Router or Switch)
    type = models.ForeignKey(DeviceType, on_delete=models.RESTRICT)

    def __str__(self):
        return self.model_name


# ======================
# DEVICE TABLE
# ======================
class Device(models.Model):
    # Human-friendly name for the device (e.g., CoreRouter1)
    hostname = models.CharField(max_length=100)

    # Device IP address (unique for each device)
    ip_address = models.CharField(max_length=45, unique=True)

    # Optional subnet mask 
    subnet_mask = models.CharField(max_length=45, blank=True, null=True)

    # References the model of this device
    model = models.ForeignKey(DeviceModel, on_delete=models.RESTRICT)

    # Optional reference to a user (e.g., who manages/added the device)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

     # credentials for SNMP access
    username = models.CharField(max_length=100, default='')
    snmp_password = models.BinaryField(default=b'')  # stores encrypted bytes (FernetKey)
    snmp_aes_passwd = models.BinaryField(default=b'')  # stores encrypted bytes (FernetKey)

    # Whether the device is actively monitored
    # is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.hostname
    
     # --- Encryption helpers ---
    def set_snmp_password(self, raw_password: str):
        """Encrypt and store password."""
        self.snmp_password = settings.FERNET.encrypt(raw_password.encode())

    def get_snmp_password(self):
        """Decrypt and return password."""
        if self.snmp_password:
            return settings.FERNET.decrypt(self.snmp_password).decode()
        return None
    
    def set_snmp_aes_passwd(self, raw_password: str):
        """Encrypt and store password."""
        self.snmp_aes_passwd = settings.FERNET.encrypt(raw_password.encode())

    def get_snmp_aes_passwd(self):
        if self.snmp_aes_passwd:
            return settings.FERNET.decrypt(self.snmp_aes_passwd).decode()


# ======================
# INTERFACE TABLE
# ======================
class Interface(models.Model):
    # Belongs to a device (e.g., a router’s interfaces)
    device = models.ForeignKey(Device, on_delete=models.CASCADE)

    # SNMP ifIndex — a unique numerical identifier for each interface
    ifIndex = models.IntegerField()

    # Interface name (e.g., GigabitEthernet0/1)
    ifName = models.CharField(max_length=100, blank=True, null=True)

    # Interface description from SNMP (optional)
    ifDescr = models.CharField(max_length=255, blank=True, null=True)

    # Custom alias or label for easier identification
    ifAlias = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        # Ensures a device cannot have duplicate ifIndex values
        unique_together = ('device', 'ifIndex')

    def __str__(self):
        # Displays both device and interface name for clarity
        return f"{self.device.hostname} - {self.ifName or self.ifDescr}"


# ======================
# OID MAP TABLE
# ======================
class OidMap(models.Model):
    # Links an SNMP OID to a specific model and metric
    model = models.ForeignKey(DeviceModel, on_delete=models.CASCADE)

    # The metric (e.g., CPU Usage, Uptime)
    metric = models.ForeignKey(Metric, on_delete=models.CASCADE)

    # The SNMP OID string (e.g., "1.3.6.1.2.1.1.3.0")
    oid = models.CharField(max_length=255)

    # Optional description for documentation
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        # Example: "Cisco 2960 / CPU Usage"
        return f"{self.model.model_name} / {self.metric.metric_name}"
    
    class Meta:
        unique_together = ('model', 'metric')  # prevents duplicates


# ======================
# HISTORY TABLE
# ======================
class History(models.Model):
    # The device this data belongs to
    device = models.ForeignKey(Device, on_delete=models.CASCADE)

    # The metric being recorded (e.g., CPU Usage)
    metric = models.ForeignKey(Metric, on_delete=models.RESTRICT)

    # Optional interface reference (for interface-based metrics like bandwidth)
    interface = models.ForeignKey(Interface, on_delete=models.CASCADE, null=True, blank=True)

    # The recorded value (e.g., 60%)
    value = models.TextField()

    # The timestamp when the data was collected
    timestamp = models.DateTimeField() 

    # Change timestamp to CharField since it's stored as a string
    # timestamp = models.CharField(max_length=255)

    class Meta:
        # Rename the table in the admin to be more readable
        verbose_name_plural = "History"


# ======================
# THRESHOLD / ALERT TABLE
# ======================
class Threshold(models.Model):
    # Device that this threshold applies to
    device = models.ForeignKey(Device, on_delete=models.CASCADE)

    # Metric being monitored (e.g., CPU Usage)
    metric = models.ForeignKey(Metric, on_delete=models.CASCADE)

    # Optional: interface-based thresholds
    interface = models.ForeignKey(Interface, on_delete=models.CASCADE, null=True, blank=True)

    # Condition type (e.g., '>', '<', '=')
    condition = models.CharField(max_length=10)

    # Threshold value to trigger alerts (e.g., "80" for 80%)
    value = models.CharField(max_length=255)

    # Alert severity level (e.g., Warning, Critical)
    alert_level = models.CharField(max_length=50, default='Warning')

    def __str__(self):
        # Example: "CoreRouter1 - CPU Usage alert"
        return f"{self.device.hostname} - {self.metric.metric_name} alert"


# ======================
# USER PREFERENCE TABLE (NEW)
# ======================
class UserPreference(models.Model):
    # Links preference to the User (one-to-one relationship)
    # primary_key=True is important for OneToOneField
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True) 
    
    # Stores the IDs of the devices the user has selected for their filter
    # We store it as text and will parse it into an array in React/Django
    selected_device_ids = models.TextField(default="",blank=True)
    
    # Stores the state of the main filter toggle (True/False)
    is_filter_active = models.BooleanField(default=False)

    def __str__(self):
        # We must include the username for display
        return f"Preferences for {self.user.username}"