from django.contrib import admin
from .models import AgentApplication
from unfold.admin import ModelAdmin

@admin.register(AgentApplication)
class AgentApplicationAdmin(ModelAdmin):
    list_display = ('name','email','company','approved','submitted_at')
    list_editable = ('approved',)
    search_fields = ('name','email','company')
