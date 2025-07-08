from django.contrib import admin
from .models import TrackingRecord

@admin.register(TrackingRecord)
class TrackingRecordAdmin(admin.ModelAdmin):
    list_display = ('booking','status','location','timestamp')
    list_filter = ('status',)
    search_fields = ('booking__id','location')
