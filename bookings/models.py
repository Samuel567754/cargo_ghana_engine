import uuid
import logging
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils.crypto import get_random_string
from datetime import datetime, time, timedelta
from django.db.models import F, Sum, ExpressionWrapper, DecimalField

logger = logging.getLogger(__name__)


def generate_reference_code():
    import random, string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


class BoxType(models.Model):
    name = models.CharField(max_length=50)
    length_cm = models.PositiveIntegerField()
    width_cm = models.PositiveIntegerField()
    height_cm = models.PositiveIntegerField()
    price_per_kg = models.DecimalField(max_digits=8, decimal_places=2)
    price_per_box = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.name

    @property
    def volume_m3(self) -> Decimal:
        return (
            Decimal(self.length_cm) / 100
            * Decimal(self.width_cm) / 100
            * Decimal(self.height_cm) / 100
        )


class Booking(models.Model):
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_code = models.CharField(
        max_length=12, unique=True, editable=False,
        default=generate_reference_code,
        help_text="Short code for customer reference"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    # **Re‑added** so that `booking.referral_id` exists
    referral = models.ForeignKey(
        'referrals.Referral',
        on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    box_type       = models.ForeignKey(BoxType, on_delete=models.PROTECT)
    quantity       = models.PositiveIntegerField(default=1)
    pickup_address = models.TextField()
    pickup_date    = models.DateField()
    pickup_slot    = models.CharField(max_length=20)
    created_at     = models.DateTimeField(auto_now_add=True)
    cost           = models.DecimalField(
        max_digits=10, decimal_places=2, editable=False,
        help_text="Computed as volume (m³) × £453.66"
    )

    def __str__(self):
        return self.reference_code

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)

        # Log capacity after save
        if is_new or 'quantity' in kwargs.get('update_fields', []):
            current_batch = ContainerBatch.objects.filter(status='open').first()
            if current_batch:
                ContainerCapacity.log_capacity(current_batch)

        # Existing notification logic
        if is_new:
            from .models import send_booking_notifications
            send_booking_notifications.delay(str(self.id))

    @classmethod
    def total_booked_volume(cls) -> Decimal:
        # Use database aggregation instead of Python loop
        result = cls.objects.annotate(
            item_volume=ExpressionWrapper(
                F('box_type__length_cm') * F('box_type__width_cm') * 
                F('box_type__height_cm') * F('quantity') / 1000000,
                output_field=DecimalField()
            )
        ).aggregate(total=Sum('item_volume'))
        return result['total'] or Decimal('0')

    @property
    def volume_m3(self) -> Decimal:
        return self.box_type.volume_m3 * self.quantity


class ContainerBatch(models.Model):
    # Add historical tracking
    volume_history = models.JSONField(default=list, help_text="Historical volume data")
    
    def update_volume_history(self):
        current_volume = Booking.total_booked_volume()
        self.volume_history.append({
            'timestamp': timezone.now().isoformat(),
            'volume': str(current_volume)
        })
        self.save(update_fields=['volume_history'])
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('ready', 'Ready to Ship'),
        ('dispatched', 'Dispatched'),
    )
    target_volume = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('66.16'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Batch #{self.id} ({self.get_status_display()})"


class NotificationLog(models.Model):
    CHANNEL_CHOICES = (
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
    )
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    recipient = models.CharField(max_length=255)
    payload = models.TextField()
    status = models.CharField(max_length=20, choices=(('success','Success'),('failed','Failed')))
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.get_channel_display()} to {self.recipient} for {self.booking or 'ADMIN'}"


# ──────────────────────────────────────────────────────────────────────────────
# Task‐proxy so tests that patch("bookings.models.send_booking_notifications.delay")
# continue to work without a circular import on module load.
class _SendBookingNotificationsProxy:
    @staticmethod
    def delay(booking_id):
        from .tasks import send_booking_notifications
        return send_booking_notifications.delay(booking_id)

send_booking_notifications = _SendBookingNotificationsProxy()


# Add this import at the top with other imports
from typing import Dict

CONTAINER_MAX_VOLUME = 65  # Maximum volume in m³ per container
MAX_BOXES_PER_TYPE = 100   # Maximum number of boxes per type per booking

# Volume-based discount tiers (volume in m³: discount percentage)
VOLUME_DISCOUNTS: Dict[Decimal, Decimal] = {
    Decimal('10.00'): Decimal('0.05'),  # 5% off for 10m³+
    Decimal('20.00'): Decimal('0.10'),  # 10% off for 20m³+
    Decimal('30.00'): Decimal('0.15'),  # 15% off for 30m³+
}


# Add after other constants
PICKUP_SLOTS = [
    ('morning', '9:00 AM - 12:00 PM'),
    ('afternoon', '12:00 PM - 3:00 PM'),
    ('evening', '3:00 PM - 6:00 PM')
]

MIN_PICKUP_DAYS = 1  # Minimum days in advance for pickup
MAX_PICKUP_DAYS = 14  # Maximum days in advance for pickup


class ContainerCapacity(models.Model):
    batch = models.ForeignKey(ContainerBatch, on_delete=models.CASCADE, related_name='capacity_logs')
    total_volume = models.DecimalField(max_digits=10, decimal_places=2)
    remaining_volume = models.DecimalField(max_digits=10, decimal_places=2)
    booking_count = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    @classmethod
    def log_capacity(cls, batch: ContainerBatch):
        total_volume = Booking.total_booked_volume()
        remaining = batch.target_volume - total_volume
        booking_count = Booking.objects.count()
        
        return cls.objects.create(
            batch=batch,
            total_volume=total_volume.quantize(Decimal('0.01')),
            remaining_volume=remaining.quantize(Decimal('0.01')),
            booking_count=booking_count
        )
