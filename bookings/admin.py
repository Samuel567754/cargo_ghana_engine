from decimal import Decimal
from django.contrib import admin
from .models import BoxType, Booking, NotificationLog, ContainerBatch
from unfold.admin import ModelAdmin
from django.db.models import Sum, Count, Q
from django.utils import timezone
from agents.models import AgentApplication  # adjust if your Agent model lives elsewhere
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(ContainerBatch)
class ContainerBatchAdmin(ModelAdmin):
    list_display = (
        'id',
        'target_volume',
        'status',
        'current_volume_display',
        'percent_full_display',
        'created_at',
    )
    readonly_fields = (
        'target_volume',
        'status',
        'created_at',
        'current_volume_display',
        'percent_full_display',
    )
    list_filter = ('status',)

    def current_volume_display(self, obj):
        # call the model’s property
        return obj.current_volume
    current_volume_display.short_description = 'Current Volume (m³)'

    def percent_full_display(self, obj):
        # call the model’s property
        return f"{obj.percent_full:.2f}%"
    percent_full_display.short_description = 'Percent Full'




@admin.register(BoxType)
class BoxTypeAdmin(ModelAdmin):
    list_display = (
        'name', 'length_cm', 'width_cm', 'height_cm',
        'price_per_kg', 'price_per_box'
    )

@admin.register(Booking)
class BookingAdmin(ModelAdmin):
    list_display = (
        'reference_code', 'user', 'box_type',
        'quantity', 'pickup_date', 'pickup_slot',
        'cost', 'created_at'
    )
    readonly_fields = ('reference_code', 'cost', 'created_at')
    search_fields = ('reference_code', 'user__username', 'pickup_address')



@admin.register(NotificationLog)
class NotificationLogAdmin(ModelAdmin):
    list_display = ('booking', 'channel', 'recipient', 'status', 'sent_at')
    list_filter = ('channel', 'status')
    search_fields = ('booking__reference_code', 'recipient')




def dashboard_callback(request, context):
    today = timezone.localdate()

    qs = Booking.objects.filter(created_at__date=today)
    context['daily_count']  = qs.count()

    # Volume from box dimensions
    total_vol = Decimal('0.00')
    for b in qs.select_related('box_type'):
        dims = b.box_type
        total_vol += (dims.length_cm * dims.width_cm * dims.height_cm) / Decimal(1_000_000)
    context['daily_volume'] = total_vol.quantize(Decimal('0.01'))

    # Top 5 customers by bookings today
    cust_stats = (
        qs.values('user__id', 'user__username')
          .annotate(bookings=Count('id'))
          .order_by('-bookings')[:5]
    )
    context['customer_stats'] = cust_stats

    # New agent applications
    context['new_applications'] = AgentApplication.objects.filter(
        submitted_at__date=today
    ).count()

    return context









