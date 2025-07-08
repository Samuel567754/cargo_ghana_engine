from django.contrib import admin
from .models import BoxType, Booking

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
