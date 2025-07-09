import uuid
import logging
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils.crypto import get_random_string

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

        if not self.reference_code:
            self.reference_code = get_random_string(12).upper()

        total_volume = self.box_type.volume_m3 * self.quantity
        self.cost     = (total_volume * Decimal("453.66")).quantize(Decimal("0.01"))

        super().save(*args, **kwargs)

        # enqueue exactly once on creation
        if is_new:
            from .models import send_booking_notifications  # proxy below
            send_booking_notifications.delay(str(self.id))

    @classmethod
    def total_booked_volume(cls) -> Decimal:
        total = Decimal('0')
        for booking in cls.objects.all():
            total += booking.box_type.volume_m3 * booking.quantity
        return total


class ContainerBatch(models.Model):
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
