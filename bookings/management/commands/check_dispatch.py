# bookings/management/commands/check_dispatch.py

from decimal import Decimal
from django.core.management.base import BaseCommand
from bookings.models import Booking

class Command(BaseCommand):
    help = (
        "Check total booked volume and flag dispatch readiness "
        "(container capacity: 66.16 m³)."
    )

    CONTAINER_CAPACITY = Decimal('66.16')

    def handle(self, *args, **options):
        total = Booking.total_booked_volume()
        if total >= self.CONTAINER_CAPACITY:
            self.stdout.write(self.style.SUCCESS(
                f"✅ Capacity reached: {total:.2f}m³ ≥ {self.CONTAINER_CAPACITY}m³ → Ready to dispatch!"
            ))
            # TODO: You could here create a Dispatch record or send a notification task.
        else:
            pct = (total / self.CONTAINER_CAPACITY * 100).quantize(Decimal('0.01'))
            self.stdout.write(self.style.WARNING(
                f"⏳ {total:.2f}m³ booked ({pct}%). "
                f"{(self.CONTAINER_CAPACITY - total):.2f}m³ remaining."
            ))
