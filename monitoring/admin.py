from django.contrib import admin
from .models import (
    Brand, DeviceType, Metric, DeviceModel, 
    Device, Interface, OidMap, History, Threshold
)

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    
    # --- Configuration for the List View ---
    list_display = ('hostname', 'ip_address', 'model', 'user')
    list_filter = ('model', 'user')
    
    # --- Configuration for the "Add/Edit" Form ---
    
    def get_readonly_fields(self, request, obj=None):
        # If 'obj' exists, it's an "Edit" page, so it make 'user' read-only.
        if obj:
            return ('user',)
        # If 'obj' is None, it's an "Add" page, it hides the 'user' field.
        # It will be set automatically in save_model().
        return ()

    def save_model(self, request, obj, form, change):
        # This auto-assigns the logged-in user when a NEW device is created.
        if not obj.pk:  # If this is a new object
            obj.user = request.user  # Assign the current logged-in user
        super().save_model(request, obj, form, change)
        
    # --- NEW PERMISSIONS LOGIC ---

    def get_queryset(self, request):
        # This function controls what is in the main list.
        
        # Get the default, full list of all devices
        qs = super().get_queryset(request)
        
        # If the logged-in user is an Admin/Superuser...
        if request.user.is_superuser:
            return qs  # ...show them everything.
        
        # Otherwise (if they are a normal User)...
        # ...filter the list to show ONLY devices where user=themselves.
        return qs.filter(user=request.user)

    def has_change_permission(self, request, obj=None):
        # This controls if a user can access the "Edit" page.
        if not obj:
            #This is on the list view, so allow access
            return True
        
        # This is the "Edit" page for a specific device ('obj').
        # Allow access ONLY if they are a superuser OR they are the owner.
        return request.user.is_superuser or obj.user == request.user

    def has_delete_permission(self, request, obj=None):
        # This controls if a user can delete a device.
        if not obj:
            # it is on the list view, so allow access
            return True
        
        # We are on the "Edit" page for a specific device.
        # Allow deletion ONLY if they are a superuser OR they are the owner.
        return request.user.is_superuser or obj.user == request.user

# ----------------------------------------------------
# Admins can edit these, but normal users won't see them
# (unless you give them permission).
# ----------------------------------------------------
admin.site.register(Brand)
admin.site.register(DeviceType)
admin.site.register(Metric)
admin.site.register(DeviceModel)
admin.site.register(Interface)
admin.site.register(OidMap)
admin.site.register(History)
admin.site.register(Threshold)