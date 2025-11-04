from django.contrib import admin
from .models import Volunteer

@admin.register(Volunteer)
class VolunteerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'availability', 'date_applied')
    list_filter = ('availability', 'date_applied')
    search_fields = ('full_name', 'email', 'phone', 'skills')
    ordering = ('-date_applied',)
    list_per_page = 20  # Pagination in admin list view
    readonly_fields = ('date_applied',)

    fieldsets = (
        ('Personal Info', {
            'fields': ('full_name', 'email', 'phone')
        }),
        ('Volunteer Details', {
            'fields': ('skills', 'availability', 'date_applied')
        }),
    )

    def has_add_permission(self, request):
        """Allow adding volunteers manually (optional)."""
        return True

    def has_change_permission(self, request, obj=None):
        """Allow editing volunteers if needed."""
        return True
