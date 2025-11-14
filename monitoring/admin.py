# monitoring/admin.py
"""
Custom Django admin configuration for the 'monitoring' app.

Features:
- BaseIconAdmin: reusable admin base that adds an "Actions" column with Edit/Delete links.
- Each model keeps its original list_display fields + actions column.
- DeviceAdmin: custom device permissions (non-superusers only see own devices).
- HistoryAdmin: read-only history view (no add/change/delete).
- MonitoringAdminSite: custom AdminSite with grouped sidebar.
- All models are registered to the custom admin site (custom_admin_site).
"""

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django import forms
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404, redirect
from .models import (
    Brand, DeviceType, Metric, DeviceModel,
    Device, Interface, OidMap, History, Threshold
)


# ----------------------------------------------------
# Base admin class to add Edit/Delete buttons
# ----------------------------------------------------
class BaseIconAdmin(admin.ModelAdmin):
    """
    Base admin for simple models to:
    - Add 'action_buttons' column for Edit/Delete links.
    - Disable default actions dropdown (delete selected).
    - Intended to be extended by other admins.
    - Respects Django permissions.
    """
    actions = None  # Remove "delete selected"

    def action_buttons(self, obj):
        change_url = reverse(
            f'admin:{obj._meta.app_label}_{obj._meta.model_name}_change',
            args=[obj.pk]
        )
        delete_url = reverse(
            f'admin:{obj._meta.app_label}_{obj._meta.model_name}_delete',
            args=[obj.pk]
        )
        buttons = []
        if self.has_change_permission(self.request, obj):
            buttons.append(f'<a href="{change_url}">✏️ Edit</a>')
        if self.has_delete_permission(self.request, obj):
            buttons.append(f'<a href="{delete_url}">❌ Delete</a>')
        return format_html(" | ".join(buttons))

    action_buttons.short_description = 'Actions'

    # Override get_queryset to store request for permission checks
    def get_queryset(self, request):
        """Store request for use in action_buttons"""
        self.request = request
        return super().get_queryset(request)

    # Permission to show model in sidebar
    def has_module_permission(self, request):
        """
        Show the model in the sidebar only if the user has at least
        one permission (view/add/change/delete)
        """
        opts = self.model._meta
        return request.user.has_perm(f'{opts.app_label}.view_{opts.model_name}') or \
               request.user.has_perm(f'{opts.app_label}.add_{opts.model_name}') or \
               request.user.has_perm(f'{opts.app_label}.change_{opts.model_name}') or \
               request.user.has_perm(f'{opts.app_label}.delete_{opts.model_name}')

# ----------------------------------------------------
# Custom AdminSite for grouped sidebar
# ----------------------------------------------------
class MonitoringAdminSite(admin.AdminSite):
    """
    Custom AdminSite that:
    - Groups models in the sidebar (Monitoring, Device Blueprints, Polling, Authentication)
    - Provides a custom header, title, and index title
    """
    site_header = "Network Device Monitoring System"
    site_title = "Monitoring Admin"
    index_title = "Network Monitoring Control Panel"

    def get_app_list(self, request, app_label=None):
        """
        Returns a custom grouped structure of models for the sidebar.
        Filters out any unregistered models to prevent empty sections.
        """
        app_list = super().get_app_list(request, app_label=app_label)
        grouped = [
            {
                "name": _("Monitoring"),
                "models": [
                    self._find_model(app_list, "Device"),
                    self._find_model(app_list, "History"),
                    self._find_model(app_list, "Interface"),
                ],
            },
            {
                "name": _("Device Blueprints"),
                "models": [
                    self._find_model(app_list, "Brand"),
                    self._find_model(app_list, "DeviceModel"),
                    self._find_model(app_list, "DeviceType"),
                ],
            },
            {
                "name": _("Polling Configuration"),
                "models": [
                    self._find_model(app_list, "Metric"),
                    self._find_model(app_list, "OidMap"),
                    self._find_model(app_list, "Threshold"),
                ],
            },
            {
                "name": _("Authentication"),
                "models": [
                    self._find_model(app_list, "Group", app_label="auth"),
                    self._find_model(app_list, "User", app_label="auth"),
                ],
            },
        ]
        # Remove any None entries
        for group in grouped:
            group["models"] = [m for m in group["models"] if m]

            #If app_label is provided,Django expects to return original ungrouped list for that app
            #Otherwise, show the custom grouped list on the main index

            if app_label:
                return app_list
            
        return grouped

    def _find_model(self, app_list, model_name, app_label="monitoring"):
        """
        Helper to find a specific model dict in the app_list.
        Returns None if not found.
        """
        for app in app_list:
            if app.get("app_label") == app_label:
                for model in app.get("models", []):
                    if model.get("object_name") == model_name:
                        return model
        return None


# Instantiate the custom admin site
custom_admin_site = MonitoringAdminSite(name="monitoring_admin")


# ----------------------------------------------------
# Simple models using BaseIconAdmin
# ----------------------------------------------------
class BrandAdmin(BaseIconAdmin):
    """
    Admin for Brand model.
    """
    list_display = ('brand_name', 'action_buttons')
    search_fields = ('brand_name',)
    
def save_model(self, request, obj, form, change):
        """Prevent creating duplicate Brand names."""
        if not change:
            if Brand.objects.filter(brand_name=obj.brand_name).exists():
                raise ValidationError("A Brand with this name already exists.")
        super().save_model(request, obj, form, change)

class DeviceTypeAdmin(BaseIconAdmin):
    """
    Admin for DeviceType model.
    """
    list_display = ('type_name', 'action_buttons')
    search_fields = ('type_name',)

    def save_model(self, request, obj, form, change):
            """Prevent creating duplicate DeviceType names."""
            if not change:
                if DeviceType.objects.filter(type_name=obj.type_name).exists():
                    raise ValidationError("A Device Type with this name already exists.")
            super().save_model(request, obj, form, change)

class MetricAdmin(BaseIconAdmin):
    """
    Admin for Metric model.
    """
    list_display = ('metric_name', 'unit', 'action_buttons')
    list_filter = ('unit',)
    search_fields = ('metric_name', 'unit')

def save_model(self, request, obj, form, change):
        """Prevent creating duplicate Metric names."""
        if not change:
            if Metric.objects.filter(metric_name=obj.metric_name).exists():
                raise ValidationError("A Metric with this name already exists.")
        super().save_model(request, obj, form, change)

custom_admin_site.register(Brand, BrandAdmin)
custom_admin_site.register(DeviceType, DeviceTypeAdmin)
custom_admin_site.register(Metric, MetricAdmin)


# --- Custom ModelForm for Device ---
class DeviceAdminForm(forms.ModelForm):
    username = forms.CharField(
        required=True,  # enforce mandatory input
        label="SNMP Username"
    )
    # Plain text fields for input
    snmp_auth_password = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        required=True,  # enforce mandatory input
        label="SNMP Auth Password"
    )
    snmp_priv_password = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        required=True,  # enforce mandatory input
        label="SNMP AES Password"
    )

    class Meta:
        model = Device
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Handle form mode
        if self.instance and self.instance.pk:
            # Editing existing device: show decrypted passwords
            self.fields['snmp_auth_password'].initial = self.instance.get_snmp_password()
            self.fields['snmp_priv_password'].initial = self.instance.get_snmp_aes_passwd()

            # When editing, mask passwords
            self.fields['snmp_auth_password'].widget = forms.PasswordInput(render_value=True)
            self.fields['snmp_priv_password'].widget = forms.PasswordInput(render_value=True)
        else:
            # Adding new device: allow visible text for easier input
            self.fields['snmp_auth_password'].widget = forms.TextInput()
            self.fields['snmp_priv_password'].widget = forms.TextInput()

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Encrypt both passwords if provided
        auth_pwd = self.cleaned_data.get('snmp_auth_password')
        priv_pwd = self.cleaned_data.get('snmp_priv_password')

        if auth_pwd:
            instance.snmp_password = settings.FERNET.encrypt(auth_pwd.encode())
        elif self.instance.pk and not auth_pwd:
            instance.snmp_password = self.instance.snmp_password  # keep existing

        if priv_pwd:
            instance.snmp_aes_passwd = settings.FERNET.encrypt(priv_pwd.encode())
        elif self.instance.pk and not priv_pwd:
            instance.snmp_aes_passwd = self.instance.snmp_aes_passwd  # keep existing

        if commit:
            instance.save()
        return instance


# ----------------------------------------------------
# DeviceAdmin with per-user permissions
# ----------------------------------------------------
class DeviceAdmin(admin.ModelAdmin):
    """
    Admin for Device model.

    Features:
    - Non-superusers can see only their devices
    - 'user' field hidden for non-superusers, editable for superusers
    - Automatically assign logged-in user if 'user' is blank
    - Actions column with Edit/Delete links
    - Remove default "delete selected" action
    """
    list_display = ('hostname', 'ip_address', 'model', 'user', 'action_buttons')
    list_filter = ('model', 'user')
    search_fields = ('hostname', 'ip_address', 'model', 'user')
    actions = None  # remove "delete selected"

    form = DeviceAdminForm # use custom form with password handling

    fields = ('hostname', 'ip_address', 'subnet_mask', 'model', 'user', 'username', 'snmp_auth_password',
        'snmp_priv_password') 

    # Tells django admin to use custom template for delete confirmation
    delete_confirmation_template = "admin/monitoring/device/delete_confirmation.html"

    def get_fields(self, request, obj=None):
        """
        Determine which fields to show in the form.
        - Non-superusers: hide 'user' field
        - Superusers: show 'user' field (optional)
        """
        fields = super().get_fields(request, obj)
        if not request.user.is_superuser:  # hide user field for normal users
            fields = [f for f in fields if f != 'user']
        return fields

    def get_readonly_fields(self, request, obj=None):
        """
        Make 'user' readonly on edit pages for everyone except superuser (editable on creation).
        """
        readonly = super().get_readonly_fields(request, obj)
        if obj and not request.user.is_superuser:
            readonly += ('user',)
        return readonly

    def save_model(self, request, obj, form, change):
        """
        Assign user automatically and prevent duplicate devices.
        - Non-superusers: always assigned to logged-in user
        - Superusers: if left blank, assign to logged-in superuser
        - Prevent creating a device with the same hostname + IP
        """
        if not obj.pk:  # only on creation
            if not obj.user:  # field left blank
                obj.user = request.user
            # Check duplicates
            if Device.objects.filter(hostname=obj.hostname, ip_address=obj.ip_address).exists():
                from django.core.exceptions import ValidationError
                raise ValidationError("A device with this hostname and IP already exists.")
        super().save_model(request, obj, form, change)

    # Validate that passwords are provided
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        auth_pwd = cleaned_data.get('snmp_auth_password')
        priv_pwd = cleaned_data.get('snmp_priv_password')

        if not username:
            raise forms.ValidationError("SNMP Username is required.")
        if not auth_pwd:
            raise forms.ValidationError("SNMP Auth Password is required.")
        if not priv_pwd:
            raise forms.ValidationError("SNMP AES Password is required.")

        return cleaned_data

    # Queryset filtering based on user
    def get_queryset(self, request):
        """Filter queryset for non-superusers to only show their devices."""
        self.request = request  # store the request so action_buttons() can access it
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)


    # Permission overrides
    def has_change_permission(self, request, obj=None):
        """Allow editing only for owner or superuser."""
        if obj is None:
            return True
        return request.user.is_superuser or obj.user == request.user

    def has_delete_permission(self, request, obj=None):
        """
        Allow deletion only if:
        - user has the 'delete_device' permission, and
        - (optionally) the device belongs to the user, or user is superuser
        """
        if not request.user.has_perm('monitoring.delete_device'):
            return False

        if obj is not None:
            # If the device has a user field, enforce ownership rule
            return request.user.is_superuser or obj.user == request.user

        # Default (changelist page): allow view but no mass delete
        return True
    
    def get_model_perms(self, request):
        """
        Control model visibility and button availability.
        If user lacks delete permission, remove the 'delete' button.            
        """
        perms = super().get_model_perms(request)
        if not request.user.has_perm('monitoring.delete_device'):
            perms['delete'] = False
        return perms
    
    # CUSTOM DELETE_VIEW METHOD (This replaces the default view)
    def delete_view(self, request, object_id, extra_context=None): 
        """
        Overrides the default delete_view to prevent pre-fetching all
        related objects, which is a major performance bottleneck 
        (taking too much time to load the delete confirmation page)

        This view *will* call self.has_delete_permission(), respecting
        all the custom logic defined above.
        """
        
        # Get the object to be deleted
        obj = get_object_or_404(self.model, pk=object_id)
        
        # Check permissions using YOUR existing method
        if not self.has_delete_permission(request, obj):
            raise PermissionDenied

        if request.method == 'POST':
            # This is the user clicking 'Yes, I'm sure'
            obj.delete()
            self.message_user(request, _(f'The device "{obj}" was deleted successfully.'), messages.SUCCESS)
            
            # Redirect back to the changelist
            return redirect(reverse(f'admin:{self.opts.app_label}_{self.opts.model_name}_changelist'))

        # This is the GET request (showing the confirmation page)
        
        # --- THIS IS THE PERFORMANCE FIX ---
        # Get the fast counts
        history_count = obj.history_set.count() # Use your related_name

        # Create the summary dictionary for our template
        summary = {
            'Device': 1,
            'History': history_count,
            # Add other related models here if needed
        }
        
        # Build the context for our custom template
        context = {
            **self.admin_site.each_context(request),
            'title': _('Are you sure?'),
            'object': obj,
            'object_name': str(obj),
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
            'summary': summary, # Pass our custom summary
            'has_permission': True,
            **(extra_context or {}),
        }

        return TemplateResponse(request, self.delete_confirmation_template, context)
        

    # Action buttons column
    def action_buttons(self, obj):
        """Render Edit/Delete buttons for each device row, respecting user permissions."""
        user = self.request.user  # store request for permission check
        change_url = reverse(
            f'admin:{obj._meta.app_label}_{obj._meta.model_name}_change',
            args=[obj.pk]
        )

        buttons = [f'<a href="{change_url}">✏️ Edit</a>']

        # Only show delete button if user has permission
        if user.has_perm('monitoring.delete_device') and (user.is_superuser or obj.user == user):
            delete_url = reverse(
                f'admin:{obj._meta.app_label}_{obj._meta.model_name}_delete',
                args=[obj.pk]
            )
            buttons.append(f'<a href="{delete_url}">❌ Delete</a>')

        return format_html(' | '.join(buttons))


    action_buttons.short_description = 'Actions'


# Register Device with custom admin site
custom_admin_site.register(Device, DeviceAdmin)


# ----------------------------------------------------
# HistoryAdmin: read-only
# ----------------------------------------------------
class HistoryAdmin(admin.ModelAdmin):
    """
    Admin for History model.
    Read-only view: no add/change/delete allowed.
    """
    list_display = ('timestamp', 'device', 'metric', 'interface', 'value')
    list_filter = ('timestamp', 'device', 'metric')
    search_fields = ('device__hostname', 'metric__metric_name')

    actions = None  # remove "delete selected"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            # No object specified → user is viewing changelist → never allow bulk delete
            return False
        # Allow deletion only during cascade delete (Device removal)
        if hasattr(obj, "device") and hasattr(obj.device, "user"):
            # Allow only if superuser or owner of the Device
            return request.user.is_superuser or obj.device.user == request.user

        # Fallback: allow only superuser if no linked device
        return request.user.is_superuser

    def local_timestamp(self, obj):
        # Converts UTC timestamp to your TIME_ZONE
        return timezone.localtime(obj.timestamp).strftime("%Y-%m-%d %H:%M:%S")
    
    local_timestamp.admin_order_field = 'timestamp'  # allows sorting
    local_timestamp.short_description = 'Timestamp'

    def get_queryset(self, request):
        """Filter history based on user: superuser sees all, normal users see only their devices."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(device__user=request.user)  # only history of the user's devices


custom_admin_site.register(History, HistoryAdmin)


# ----------------------------------------------------
# Remaining models using BaseIconAdmin
# ----------------------------------------------------
class DeviceModelAdmin(BaseIconAdmin):
    """
    Admin for DeviceModel.
    """
    list_display = ('model_name', 'brand', 'type', 'action_buttons')
    list_filter = ('brand', 'type')
    search_fields = ('model_name', 'brand', 'type')
    
def save_model(self, request, obj, form, change):
        """Prevent creating duplicate DeviceModel names."""
        if not change:
            if DeviceModel.objects.filter(model_name=obj.model_name).exists():
                raise ValidationError("A Device Model with this name already exists.")
        super().save_model(request, obj, form, change)

class InterfaceAdmin(BaseIconAdmin):
    """
    Admin for Interface.
    """
    list_display = ('device', 'ifIndex', 'ifName', 'ifDescr', 'ifAlias', 'action_buttons')
    list_filter = ('device',)
    search_fields = ('device__hostname', 'ifName', 'ifDescr', 'ifAlias')


class OidMapAdmin(BaseIconAdmin):
    """
    Admin for OidMap (maps model -> metric -> oid).
    """
    list_display = ('model', 'metric', 'oid', 'description', 'action_buttons')
    list_filter = ('model', 'metric', 'oid')
    search_fields = ('model', 'metric', 'oid')


class ThresholdAdmin(BaseIconAdmin):
    """
    Admin for Threshold rules.
    """
    list_display = ('device', 'metric', 'interface', 'condition', 'value', 'alert_level', 'action_buttons')
    list_filter = ('device', 'metric', 'interface', 'condition', 'value', 'alert_level')
    search_fields = ('device', 'metric', 'interface', 'condition', 'value', 'alert_level')

custom_admin_site.register(DeviceModel, DeviceModelAdmin)
custom_admin_site.register(Interface, InterfaceAdmin)
custom_admin_site.register(OidMap, OidMapAdmin)
custom_admin_site.register(Threshold, ThresholdAdmin)


# ----------------------------------------------------
# Django auth models
# ----------------------------------------------------
custom_admin_site.register(Group)

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

@admin.register(User, site=custom_admin_site)
class UserAdmin(BaseUserAdmin):
    """
    Custom User admin under custom admin site.
    """
    actions = None  # remove "delete selected"
    list_display = ('username', 'email', 'is_staff', 'is_superuser', 'is_active',)
    list_filter = ('is_superuser', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('username',)

    def save_model(self, request, obj, form, change):
        """Prevent duplicate username creation"""
        if not change:  # only on creation
            if User.objects.filter(username=obj.username).exists():
                from django.core.exceptions import ValidationError
                raise ValidationError("This username already exists.")
        super().save_model(request, obj, form, change)

