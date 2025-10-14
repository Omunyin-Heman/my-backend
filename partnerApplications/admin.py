from django.contrib import admin
from .models import Partners

@admin.register(Partners)
class PartnersAdmin(admin.ModelAdmin):
    list_display = ('organization_name', 'contact_person', 'email', 'phone', 'date_applied')
    list_filter = ('date_applied',)
    search_fields = ('organization_name', 'contact_person', 'email')