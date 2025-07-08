from django.contrib import admin
from .models import AgentApplication

@admin.register(AgentApplication)
class AgentApplicationAdmin(admin.ModelAdmin):
    list_display = ('name','email','company','approved','submitted_at')
    list_editable = ('approved',)
    search_fields = ('name','email','company')
