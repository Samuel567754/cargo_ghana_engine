from django.contrib import admin
from .models import BoxType, Booking, NotificationLog, ContainerBatch



@admin.register(ContainerBatch)
class ContainerBatchAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'target_volume',
        'status',
        'current_volume',
        'percent_full',
        'created_at',
    )
    list_filter = ('status',)
    readonly_fields = ('current_volume', 'percent_full', 'created_at')
    ordering = ('-created_at',)
    search_fields = ('id',)


@admin.register(BoxType)
class BoxTypeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'length_cm', 'width_cm', 'height_cm',
        'price_per_kg', 'price_per_box'
    )

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'reference_code', 'user', 'box_type',
        'weight_kg', 'pickup_date', 'pickup_slot',
        'cost', 'created_at'
    )
    readonly_fields = ('reference_code', 'cost', 'created_at')
    search_fields = ('reference_code', 'user__username', 'pickup_address')



@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('booking', 'channel', 'recipient', 'status', 'sent_at')
    list_filter = ('channel', 'status')
    search_fields = ('booking__reference_code', 'recipient')
