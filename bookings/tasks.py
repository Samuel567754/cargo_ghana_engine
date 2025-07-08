import os
from decimal import Decimal
from celery import shared_task
from django.core.mail import send_mail

# env variables
ADMIN_EMAIL    = os.getenv('ADMIN_EMAIL')
TWILIO_SID     = os.getenv('TWILIO_SID')
TWILIO_TOKEN   = os.getenv('TWILIO_TOKEN')
TWILIO_FROM    = os.getenv('TWILIO_FROM')
ADMIN_WHATSAPP = os.getenv('ADMIN_WHATSAPP')

MILESTONES = [Decimal('0.25'), Decimal('0.50'), Decimal('0.75')]
CONTAINER_CAPACITY = Decimal('66.16')

@shared_task
def send_booking_notifications(booking_id):
    # import inside to avoid circular import
    from .models import Booking
    b = Booking.objects.get(pk=booking_id)

    # send email
    recipient = b.user.email if b.user and b.user.email else ADMIN_EMAIL
    send_mail(
        subject=f'Booking Confirmed: {b.reference_code}',
        message=(
            f'Your booking {b.reference_code} is confirmed.\n'
            f'Box: {b.box_type.name}\n'
            f'Pickup: {b.pickup_date} ({b.pickup_slot})\n'
            f'Cost: GHS {b.cost}'
        ),
        from_email='no-reply@cargoghana.com',
        recipient_list=[recipient],
    )

    # optional WhatsApp
    try:
        from twilio.rest import Client
    except ImportError:
        Client = None

    if Client and TWILIO_SID and TWILIO_TOKEN and ADMIN_WHATSAPP:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        client.messages.create(
            body=(
                f'New booking {b.reference_code}: '
                f'{b.box_type.name}, {b.weight_kg}kg, GHS {b.cost}'
            ),
            from_=f'whatsapp:{TWILIO_FROM}',
            to=f'whatsapp:{ADMIN_WHATSAPP}',
        )

@shared_task
def check_milestones_and_notify():
    from .models import Booking
    total = Booking.total_booked_volume()
    for m in MILESTONES:
        threshold = (CONTAINER_CAPACITY * m).quantize(Decimal('0.01'))
        if threshold - Decimal('0.01') < total <= threshold + Decimal('0.01'):
            pct = int(m * 100)
            send_mail(
                subject=f'{pct}% Container Booked',
                message=f'{total:.2f}m³ of {CONTAINER_CAPACITY}m³ reached ({pct}%).',
                from_email='no-reply@cargoghana.com',
                recipient_list=[ADMIN_EMAIL],
            )

@shared_task
def notify_dispatch_ready():
    from .models import Booking
    total = Booking.total_booked_volume()
    if total >= CONTAINER_CAPACITY:
        send_mail(
            subject='Container Ready to Dispatch',
            message=f'All {CONTAINER_CAPACITY}m³ booked—ready to dispatch!',
            from_email='no-reply@cargoghana.com',
            recipient_list=[ADMIN_EMAIL],
        )
        try:
            from twilio.rest import Client
        except ImportError:
            Client = None

        if Client and TWILIO_SID and TWILIO_TOKEN and ADMIN_WHATSAPP:
            client = Client(TWILIO_SID, TWILIO_TOKEN)
            client.messages.create(
                body='Container filled—ready to dispatch!',
                from_=f'whatsapp:{TWILIO_FROM}',
                to=f'whatsapp:{ADMIN_WHATSAPP}',
            )
