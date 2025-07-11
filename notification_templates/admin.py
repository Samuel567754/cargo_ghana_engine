from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from .models import NotificationTemplate

class NotificationTemplateResource(resources.ModelResource):
    class Meta:
        model = NotificationTemplate
        fields = ('id', 'name', 'channel', 'is_active', 'description', 
                 'subject', 'body', 'created_at', 'updated_at')

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(ImportExportModelAdmin):
    resource_class = NotificationTemplateResource
    list_display = ('name', 'channel', 'is_active', 'updated_at')
    list_filter = ('channel', 'is_active')
    search_fields = ('name', 'description', 'subject', 'body')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'channel', 'is_active')
        }),
        ('Template Content', {
            'fields': ('subject', 'body'),
            'description': 'Use {{variable}} syntax for template variables'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
