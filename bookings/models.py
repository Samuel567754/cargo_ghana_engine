import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils.crypto import get_random_string

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
            except (ImportError, NameError):
                # In test environments or if Celery isn’t configured, just skip
                pass





# import uuid
# from decimal import Decimal
# from django.db import models
# from django.conf import settings
# from django.utils.crypto import get_random_string

# def generate_reference_code():
#     import random, string
#     return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# class BoxType(models.Model):
#     name = models.CharField(max_length=50)
#     length_cm = models.PositiveIntegerField()
#     width_cm = models.PositiveIntegerField()
#     height_cm = models.PositiveIntegerField()
#     price_per_kg = models.DecimalField(max_digits=8, decimal_places=2)
#     price_per_box = models.DecimalField(max_digits=8, decimal_places=2)

#     def __str__(self):
#         return self.name

#     @property
#     def volume_m3(self) -> Decimal:
#         return (Decimal(self.length_cm) / 100) * \
#                (Decimal(self.width_cm)  / 100) * \
#                (Decimal(self.height_cm) / 100)


# class Booking(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     reference_code = models.CharField(
#         max_length=12,
#         unique=True,
#         editable=False,
#         default=generate_reference_code,
#         help_text="Short code for customer reference"
#     )
#     user = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.SET_NULL, null=True, blank=True
#     )
#     box_type = models.ForeignKey(BoxType, on_delete=models.PROTECT)
#     weight_kg = models.DecimalField(max_digits=6, decimal_places=2)
#     pickup_address = models.TextField()
#     pickup_date = models.DateField()
#     pickup_slot = models.CharField(max_length=20)
#     created_at = models.DateTimeField(auto_now_add=True)
#     cost = models.DecimalField(
#         max_digits=10, decimal_places=2,
#         editable=False, help_text="Automatically computed"
#     )

#     def __str__(self):
#         return self.reference_code

#     @property
#     def volume(self) -> Decimal:
#         return self.box_type.volume_m3

#     @classmethod
#     def total_booked_volume(cls) -> Decimal:
#         agg = cls.objects.aggregate(
#             total=models.Sum(
#                 models.F('box_type__length_cm') / 100 *
#                 models.F('box_type__width_cm')  / 100 *
#                 models.F('box_type__height_cm') / 100
#             )
#         )
#         return agg['total'] or Decimal(0)

#     def save(self, *args, **kwargs):
#         is_new = self._state.adding
#         # ensure reference_code
#         if not self.reference_code:
#             self.reference_code = get_random_string(12).upper()
#         # compute cost
#         self.cost = (
#             self.box_type.price_per_box +
#             (self.weight_kg * self.box_type.price_per_kg)
#         )
#         super().save(*args, **kwargs)
#         # send async notifications on create
#         if is_new:
#             send_booking_notifications.delay(str(self.id))
