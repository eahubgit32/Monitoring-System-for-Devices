from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import (
    Brand, DeviceType, Metric, DeviceModel, 
    Device, Interface, OidMap, History, Threshold
)

# ----------------------------------------------------
# A "Base" class to add Edit/Delete icons
# ----------------------------------------------------
class BaseIconAdmin(admin.ModelAdmin):
    """
    This is a "base class" we can reuse. It adds our custom
    'action_buttons' column to any model that inherits it.
    """
    
    # --- THIS LINE WAS REMOVED ---
    # list_display = ('name_field', 'action_buttons') 
    # ^^^ THIS WAS CAUSING THE CRASH.
    # We will *only* use the 'get_list_display' function below.

    def get_list_display(self, request):
        """
        This function is called by Django to get the list of columns.
        It dynamically finds the correct 'name' field
        (e.g., 'brand_name' or 'type_name') for the model.
        """
        if hasattr(self.model, 'brand_name'):
            name_field = 'brand_name'
        elif hasattr(self.model, 'type_name'):
            name_field = 'type_name'
        elif hasattr(self.model, 'metric_name'):
            name_field = 'metric_name'
        else:
            # Fallback if we can't find a name
            name_field = '__str__' # This shows the default string name
            
        # Return the final tuple of columns to display
        return (name_field, 'action_buttons')

    def action_buttons(self, obj):
        """
        Renders Edit (✏️) and Delete (❌) icons.
        'obj' is the item in the row (e.g., the "Cisco" brand).
        """
        
        # 'reverse' finds the URL for a specific admin page
        change_url = reverse(
            f'admin:{obj._meta.app_label}_{obj._meta.model_name}_change', 
            args=[obj.pk]
        )
        delete_url = reverse(
            f'admin:{obj._meta.app_label}_{obj._meta.model_name}_delete', 
            args=[obj.pk]
        )
        
        # 'format_html' safely renders HTML
        return format_html(
            '<a href="{}">✏️ Edit</a> | <a href="{}">❌ Delete</a>',
            change_url,
            delete_url
        )
    # This sets the human-readable column header name
    action_buttons.short_description = 'Actions'


# Register the simple models using the new BaseIconAdmin
@admin.register(Brand)
class BrandAdmin(BaseIconAdmin):
    pass

@admin.register(DeviceType)
class DeviceTypeAdmin(BaseIconAdmin):
    pass

@admin.register(Metric)
class MetricAdmin(BaseIconAdmin):
    pass

# ----------------------------------------------------
# Custom "Device" admin with permissions
# ----------------------------------------------------
@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    
    # --- Configuration for the List View ---
    list_display = ('hostname', 'ip_address', 'model', 'user', 'action_buttons')
    list_filter = ('model', 'user')
    
    # --- Configuration for the "Add/Edit" Form ---
    
    def get_readonly_fields(self, request, obj=None):
        """
        This controls which fields are "read-only" on the edit page.
        """
        if obj: # If this is an "Edit" page (obj exists)
            return ('user',) # Make 'user' read-only
        return () # On an "Add" page, no fields are read-only

    def save_model(self, request, obj, form, change):
        """
        This is called when an admin clicks "Save".
        """
        if not obj.pk: # If this is a new device
            obj.user = request.user # Assign the logged-in user as the owner
        super().save_model(request, obj, form, change)
        
    # --- PERMISSIONS LOGIC ---

    def get_queryset(self, request):
        """
        This controls which devices appear in the list.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser: # If Admin
            return qs  # Show all devices
        return qs.filter(user=request.user) # If User, show only their own

    def has_change_permission(self, request, obj=None):
        """
        This controls who can access the "Edit" page for a device.
        """
        if not obj: # We are on the list view
            return True
        # We are on an "Edit" page
        return request.user.is_superuser or obj.user == request.user

    def has_delete_permission(self, request, obj=None):
        """
        This controls who can delete a device.
        """
        if not obj: # We are on the list view
            return True
        # We are on an "Edit" page
        return request.user.is_superuser or obj.user == request.user

    # --- ACTIONS ICON COLUMN ---
    
    def action_buttons(self, obj):
        """
        Custom actions column just for the Device list.
        """
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
            change_url,
            delete_url
        )
    action_buttons.short_description = 'Actions'


# ----------------------------------------------------
# Register the remaining models normally
# ----------------------------------------------------
admin.site.register(DeviceModel)
admin.site.register(Interface)
admin.site.register(OidMap)
admin.site.register(History)
admin.site.register(Threshold)