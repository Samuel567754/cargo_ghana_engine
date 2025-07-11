from import_export import resources
from import_export.admin import ImportExportModelAdmin
from decimal import Decimal
from django.contrib import admin
from .models import BoxType, Booking, NotificationLog, ContainerBatch

class BoxTypeResource(resources.ModelResource):
    class Meta:
        model = BoxType
        fields = ('id', 'name', 'length_cm', 'width_cm', 'height_cm', 'price_per_kg', 'price_per_box')

class BookingResource(resources.ModelResource):
    class Meta:
        model = Booking
        fields = ('id', 'reference_code', 'user__username', 'box_type__name', 'quantity', 'pickup_date', 
                 'pickup_slot', 'cost', 'created_at', 'pickup_address')

class NotificationLogResource(resources.ModelResource):
    class Meta:
        model = NotificationLog
        fields = ('id', 'booking__reference_code', 'channel', 'recipient', 'status', 'sent_at')

class ContainerBatchResource(resources.ModelResource):
    class Meta:
        model = ContainerBatch
        fields = ('id', 'target_volume', 'status', 'created_at')

@admin.register(ContainerBatch)
class ContainerBatchAdmin(ImportExportModelAdmin):
    resource_class = ContainerBatchResource
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
class BoxTypeAdmin(ImportExportModelAdmin):
    resource_class = BoxTypeResource
    list_display = (
        'name', 'length_cm', 'width_cm', 'height_cm',
        'price_per_kg', 'price_per_box'
    )

@admin.register(Booking)
class BookingAdmin(ImportExportModelAdmin):
    resource_class = BookingResource
    list_display = (
        'reference_code', 'user', 'box_type',
        'quantity', 'pickup_date', 'pickup_slot',
        'cost', 'created_at'
    )
    readonly_fields = ('reference_code', 'cost', 'created_at')
    search_fields = ('reference_code', 'user__username', 'pickup_address')



@admin.register(NotificationLog)
class NotificationLogAdmin(ImportExportModelAdmin):
    resource_class = NotificationLogResource
    list_display = ('booking', 'channel', 'recipient', 'status', 'sent_at')
    list_filter = ('channel', 'status')
    search_fields = ('booking__reference_code', 'recipient')




def dashboard_callback(request, context):
    today = timezone.localdate()
    this_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Daily metrics
    daily_bookings = Booking.objects.filter(created_at__date=today)
    context['daily_count'] = daily_bookings.count()
    context['daily_revenue'] = daily_bookings.aggregate(total=Sum('cost'))['total'] or 0

    # Monthly metrics
    monthly_bookings = Booking.objects.filter(created_at__gte=this_month)
    context['monthly_count'] = monthly_bookings.count()
    context['monthly_revenue'] = monthly_bookings.aggregate(total=Sum('cost'))['total'] or 0

    # Volume calculations
    total_vol = Decimal('0.00')
    for b in daily_bookings.select_related('box_type'):
        dims = b.box_type
        total_vol += (dims.length_cm * dims.width_cm * dims.height_cm) / Decimal(1_000_000)
    context['daily_volume'] = total_vol.quantize(Decimal('0.01'))

    # Top 5 customers by bookings today
    context['customer_stats'] = (
        daily_bookings.values('user__id', 'user__username')
          .annotate(bookings=Count('id'), revenue=Sum('cost'))
          .order_by('-bookings')[:5]
    )

    # Status distribution
    context['status_distribution'] = (
        TrackingRecord.objects.filter(booking__created_at__date=today)
        .values('status')
        .annotate(count=Count('id'))
        .order_by('status')
    )

    # Agent performance
    context['agent_performance'] = (
        daily_bookings.filter(user__is_agent=True)
        .values('user__username')
        .annotate(
            bookings=Count('id'),
            revenue=Sum('cost'),
            avg_booking_value=Avg('cost')
        ).order_by('-revenue')[:5]
    )

    # New agent applications
    context['new_applications'] = AgentApplication.objects.filter(
        submitted_at__date=today
    ).count()

    return context









