from django.contrib import admin
from .models import TrackingRecord
from unfold.admin import ModelAdmin

@admin.register(TrackingRecord)
class TrackingRecordAdmin(ModelAdmin):
    list_display = ('booking','status','location','timestamp')
    list_filter = ('status',)
    search_fields = ('booking__id','location')
