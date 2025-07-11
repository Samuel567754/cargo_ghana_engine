from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from .models import AgentApplication

class AgentApplicationResource(resources.ModelResource):
    class Meta:
        model = AgentApplication
        fields = ('id', 'name', 'email', 'phone', 'company', 'status', 
                 'submitted_at', 'reviewed_at')

@admin.register(AgentApplication)
class AgentApplicationAdmin(ImportExportModelAdmin):
    resource_class = AgentApplicationResource
    list_display = (
        'name', 'email', 'phone', 'company',
        'status', 'submitted_at', 'reviewed_at'
    )
    list_filter = ('status', 'submitted_at', 'reviewed_at')
    search_fields = ('name', 'email', 'phone', 'company')
    readonly_fields = ('submitted_at', 'reviewed_at')
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'email', 'phone', 'company')
        }),
        ('Application Details', {
            'fields': ('experience', 'id_document', 'business_license', 'resume')
        }),
        ('Review Status', {
            'fields': (
                'status', 'submitted_at', 'reviewed_at',
                'reviewed_by', 'admin_notes'
            )
        })
    )

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            obj.reviewed_at = timezone.now()
            obj.reviewed_by = request.user
        super().save_model(request, obj, form, change)
