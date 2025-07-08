import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils.crypto import get_random_string
import logging
from django.utils import timezone

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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_code = models.CharField(
        max_length=12,
        unique=True,
        editable=False,
        default=generate_reference_code,
        help_text="Short code for customer reference"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    box_type = models.ForeignKey(BoxType, on_delete=models.PROTECT)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2)
    pickup_address = models.TextField()
    pickup_date = models.DateField()
    pickup_slot = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False,
        help_text="Automatically computed"
    )

    def __str__(self):
        return self.reference_code

    @property
    def volume(self) -> Decimal:
        return self.box_type.volume_m3

    @classmethod
    def total_booked_volume(cls) -> Decimal:
        # Sum up every box's volume
        agg = cls.objects.aggregate(
            total=models.Sum(
                models.F('box_type__length_cm') / 100
                * models.F('box_type__width_cm') / 100
                * models.F('box_type__height_cm') / 100
            )
        )
        return agg['total'] or Decimal(0)

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        # Ensure we have a reference code
        if not self.reference_code:
            self.reference_code = get_random_string(12).upper()

        # Compute cost = price_per_box + (weight × price_per_kg)
        self.cost = (
            self.box_type.price_per_box
            + (self.weight_kg * self.box_type.price_per_kg)
        )

        # Save first so we have an ID
        super().save(*args, **kwargs)

        # Only on creation, fire off the Celery task
        if is_new:
            try:
                # Import inside method to avoid circular import
                from .tasks import send_booking_notifications
                send_booking_notifications.delay(str(self.id))
            except Exception as e:
                # Swallow any errors (e.g. Twilio auth failures) but log for debugging
                logger.warning(f"send_booking_notifications failed for Booking {self.id}: {e}")

            



class ContainerBatch(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('ready', 'Ready to Ship'),
        ('dispatched', 'Dispatched'),
    )

    target_volume = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Target volume (m³) for this container batch"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Batch #{self.id} ({self.get_status_display()})"

    @property
    def current_volume(self):
        """
        Sum of all booking volumes (box_type.volume_m3 * booking.quantity)
        for bookings created while this batch is 'open'.
        """
        from .models import Booking  # avoid circular imports
        bookings = Booking.objects.filter(
            created_at__gte=self.created_at,
            status__in=['pending', 'confirmed']
        )
        total = Decimal('0')
        for b in bookings:
            total += Decimal(b.box_type.volume_m3) * b.quantity
        return total

    @property
    def percent_full(self):
        if not self.target_volume:
            return 0
        return float((self.current_volume / self.target_volume) * 100)




class NotificationLog(models.Model):
    CHANNEL_CHOICES = (
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
    )

    booking = models.ForeignKey(
        'Booking',
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    recipient = models.CharField(max_length=255)
    payload = models.TextField(help_text="Raw message body or JSON payload")
    status = models.CharField(
        max_length=20,
        choices=(('success', 'Success'), ('failed', 'Failed'))
    )
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.get_channel_display()} to {self.recipient} for {self.booking.reference_code}"



