# monitoring/admin.py
"""
Custom Django admin configuration for the 'monitoring' app.

Features:
- BaseIconAdmin: reusable admin base that adds an "Actions" column with Edit/Delete links.
- DeviceAdmin: custom device permissions (non-superusers only see own devices).
- HistoryAdmin: read-only history view (no add/change/delete).
- MonitoringAdminSite: custom AdminSite that groups models into logical sections
  (Monitoring, Device Blueprints, Polling Configuration, Authentication).
- All models are registered to the custom admin site (custom_admin_site).
"""

from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import (
    Brand, DeviceType, Metric, DeviceModel,
    Device, Interface, OidMap, History, Threshold
)


# ----------------------------------------------------
# Reusable Base class that adds an "Actions" column
# ----------------------------------------------------
class BaseIconAdmin(admin.ModelAdmin):
    """
    Base admin class to reuse an 'action_buttons' column across simple models.
    It dynamically chooses a sensible 'name' field for the list display
    (brand_name, type_name, metric_name, or __str__ fallback).
    """

    def get_list_display(self, request):
        """
        Dynamically decide which 'name' field to show (so this base can be reused).
        Returns a tuple of (name_field, 'action_buttons').
        """
        # Determine sensible name field for the current model
        if hasattr(self.model, 'brand_name'):
            name_field = 'brand_name'
        elif hasattr(self.model, 'type_name'):
            name_field = 'type_name'
        elif hasattr(self.model, 'metric_name'):
            name_field = 'metric_name'
        else:
            # fallback to model's __str__ representation
            name_field = '__str__'

        return (name_field, 'action_buttons')

    def action_buttons(self, obj):
        """
        Render Edit and Delete links for each row in the list view.
        We use reverse(...) to build correct admin URLs.
        """
        change_url = reverse(
            f'admin:{obj._meta.app_label}_{obj._meta.model_name}_change',
            args=[obj.pk]
        )
        delete_url = reverse(
            f'admin:{obj._meta.app_label}_{obj._meta.model_name}_delete',
            args=[obj.pk]
        )

        # format_html safely outputs HTML into Django admin list cell
        return format_html(
            '<a href="{}">✏️ Edit</a> | <a href="{}">❌ Delete</a>',
            change_url, delete_url
        )

    action_buttons.short_description = 'Actions'


# ----------------------------------------------------
# Custom AdminSite: group and order the sidebar items
# ----------------------------------------------------
class MonitoringAdminSite(admin.AdminSite):
    """
    Custom AdminSite that reorders and groups the models into logical sections.
    The `get_app_list` method returns a custom list structure representing groups.
    """
    site_header = "Django Administration"
    site_title = "Monitoring Admin"
    index_title = "Network Monitoring Control Panel"

    def get_app_list(self, request):
        """
        Build a grouped app/model list for the sidebar. This returns a list of
        group-dictionaries (name + models). We look up registered models
        from the default app_list returned by the parent.
        """
        app_list = super().get_app_list(request)

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

        # strip out any None models (not registered) to avoid empty entries
        for group in grouped:
            group["models"] = [m for m in group["models"] if m]

        return grouped

    def _find_model(self, app_list, model_name, app_label="monitoring"):
        """
        Helper: find a specific model dictionary in the app_list by object_name.
        Returns the model dict or None.
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
# Register simple models reusing BaseIconAdmin
# ----------------------------------------------------
class BrandAdmin(BaseIconAdmin):
    """Admin for Brand model (simple listing with action icons)."""
    # Extra niceties can be added (search_fields, list_filter) as needed.
    pass

class DeviceTypeAdmin(BaseIconAdmin):
    """Admin for DeviceType model (simple listing with action icons)."""
    pass

class MetricAdmin(BaseIconAdmin):
    """Admin for Metric model (simple listing with action icons)."""
    pass


# Register them with the custom admin site
custom_admin_site.register(Brand, BrandAdmin)
custom_admin_site.register(DeviceType, DeviceTypeAdmin)
custom_admin_site.register(Metric, MetricAdmin)


# ----------------------------------------------------
# DeviceAdmin: custom list, permissions, and action icons
# ----------------------------------------------------
class DeviceAdmin(admin.ModelAdmin):
    """
    Admin for Device model with:
    - list view columns including action buttons
    - per-user visibility (non-superusers see only their devices)
    - make 'user' readonly on edit pages
    - automatically assign current user when creating new device in admin
    """

    list_display = ('hostname', 'ip_address', 'model', 'user', 'action_buttons')
    list_filter = ('model', 'user')
    search_fields = ('hostname', 'ip_address')

    def get_readonly_fields(self, request, obj=None):
        """
        On edit (obj exists) make the 'user' field readonly so ownership is preserved.
        """
        if obj:
            return ('user',)
        return ()

    def save_model(self, request, obj, form, change):
        """
        When a new Device is created in admin, set the owner/user to the logged-in user.
        """
        if not obj.pk:
            obj.user = request.user
        super().save_model(request, obj, form, change)

    # --- Permissions logic to restrict edit/delete to owner or superuser ---
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def has_change_permission(self, request, obj=None):
        # allow list view; for object-level ensure owner or superuser
        if obj is None:
            return True
        return request.user.is_superuser or obj.user == request.user

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return True
        return request.user.is_superuser or obj.user == request.user

    # --- Actions column specific for Devices ---
    def action_buttons(self, obj):
        change_url = reverse(
            f'admin:{obj._meta.app_label}_{obj._meta.model_name}_change',
            args=[obj.pk]
        )
        delete_url = reverse(
            f'admin:{obj._meta.app_label}_{obj._meta.model_name}_delete',
            args=[obj.pk]
        )
        return format_html(
            '<a href="{}">✏️ Edit</a> | <a href="{}">❌ Delete</a>',
            change_url, delete_url
        )

    action_buttons.short_description = 'Actions'


# Register Device with custom admin site
custom_admin_site.register(Device, DeviceAdmin)


# ----------------------------------------------------
# HistoryAdmin: read-only in admin
# ----------------------------------------------------
class HistoryAdmin(admin.ModelAdmin):
    """
    Make History read-only from admin; no add/change/delete allowed.
    Useful so operators can browse collected records but not alter them.
    """
    list_display = ('timestamp', 'device', 'metric', 'interface', 'value')
    list_filter = ('timestamp', 'device', 'metric')
    search_fields = ('device__hostname', 'metric__metric_name')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        # Prevent editing individual history entries
        return False

    def has_delete_permission(self, request, obj=None):
        return False


custom_admin_site.register(History, HistoryAdmin)


# ----------------------------------------------------
# Register remaining models with sensible defaults
# ----------------------------------------------------
class DeviceModelAdmin(admin.ModelAdmin):
    """Admin for DeviceModel (blueprint for devices)."""
    list_display = ('model_name', 'brand', 'type')
    list_filter = ('brand', 'type')
    search_fields = ('model_name',)

class InterfaceAdmin(admin.ModelAdmin):
    """Admin for Interface records."""
    list_display = ('device', 'ifIndex', 'ifName', 'ifDescr', 'ifAlias')
    search_fields = ('device__hostname', 'ifName', 'ifDescr')

class OidMapAdmin(admin.ModelAdmin):
    """Admin for OidMap: maps model -> metric -> oid."""
    list_display = ('model', 'metric', 'oid', 'description')
    search_fields = ('oid', 'description')

class ThresholdAdmin(admin.ModelAdmin):
    """Admin for Threshold rules."""
    list_display = ('device', 'metric', 'interface', 'condition', 'value', 'alert_level')
    search_fields = ('device__hostname', 'metric__metric_name')

custom_admin_site.register(DeviceModel, DeviceModelAdmin)
custom_admin_site.register(Interface, InterfaceAdmin)
custom_admin_site.register(OidMap, OidMapAdmin)
custom_admin_site.register(Threshold, ThresholdAdmin)


from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# ----------------------------------------------------
# Register Django auth models properly to restore permissions
# ----------------------------------------------------
custom_admin_site.register(Group)

@admin.register(User, site=custom_admin_site)
class UserAdmin(BaseUserAdmin):
    """
    Custom registration of the User model under the custom admin site.
    Retains all permission-related fields such as is_superuser, is_staff, groups, and permissions.
    """
    fieldsets = BaseUserAdmin.fieldsets
    add_fieldsets = BaseUserAdmin.add_fieldsets
    list_display = ('username', 'email', 'is_staff', 'is_superuser', 'is_active')
    list_filter = ('is_superuser', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('username',)



# ----------------------------------------------------
# NOTE TO DEVELOPER
# ----------------------------------------------------
# To use this custom admin site, update your project's urls.py:
#
#    # project/urls.py
#    from django.urls import path, include
#    from monitoring.admin import custom_admin_site
#
#    urlpatterns = [
#        path('admin/', custom_admin_site.urls),
#        # ... other urls ...
#    ]
#
# If you keep the default admin.site in urls.py, you will *not* see the grouped sidebar.
#
# End of file.
