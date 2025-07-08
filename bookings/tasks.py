import os
from decimal import Decimal
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.mail import send_mail
from twilio.rest import Client as TwilioClient

from .models import Booking, NotificationLog

logger = get_task_logger(__name__)

# Milestone thresholds (fractions of total capacity)
MILESTONES = [
    Decimal('0.25'),
    Decimal('0.50'),
    Decimal('0.75'),
]
CONTAINER_CAPACITY = Decimal('66.16')


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_booking_notifications(self, booking_id):
    """
    Sends booking confirmation via email and WhatsApp, with logging.
    Retries up to 3× on failure.
    """
    try:
        # only select the user; drop user__profile
        booking = Booking.objects.select_related('user').get(id=booking_id)
    except Booking.DoesNotExist as exc:
        logger.error(f'Booking {booking_id} not found: {exc}')
        return

    # 1) EMAIL (unchanged)…
    try:
        subject = f"Booking Confirmed: {booking.reference_code}"
        body = (
            f"Hello {booking.user.get_full_name()},\n\n"
            f"Your booking {booking.reference_code} has been received.\n"
            f"Pickup: {booking.pickup_date} at {booking.pickup_slot}\n"
            f"Total Cost: GHS {booking.cost}\n\nThank you!"
        )
        recipient = booking.user.email
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
            fail_silently=False,
        )
        NotificationLog.objects.create(
            booking=booking,
            channel='email',
            recipient=recipient,
            payload=body,
            status='success'
        )
    except Exception as exc:
        NotificationLog.objects.create(
            booking=booking,
            channel='email',
            recipient=booking.user.email,
            payload=body,
            status='failed',
            error_message=str(exc)
        )
        logger.exception("Failed to send booking email")
        raise self.retry(exc=exc)

    # 2) WHATSAPP
    # try to get profile.whatsapp_number, if it exists
    wa_number = None
    try:
        wa_number = booking.user.profile.whatsapp_number
    except Exception:
        wa_number = None

    if wa_number:
        try:
            tw_client = TwilioClient(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
            wa_body = (
                f"Your booking {booking.reference_code} is confirmed!\n"
                f"Pickup: {booking.pickup_date} at {booking.pickup_slot}\n"
                f"Cost: GHS {booking.cost}"
            )
            wa_from = f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}"
            wa_to   = f"whatsapp:{wa_number}"

            tw_client.messages.create(body=wa_body, from_=wa_from, to=wa_to)
            NotificationLog.objects.create(
                booking=booking,
                channel='whatsapp',
                recipient=wa_to,
                payload=wa_body,
                status='success'
            )
        except Exception as exc:
            NotificationLog.objects.create(
                booking=booking,
                channel='whatsapp',
                recipient=wa_number,
                payload=wa_body,
                status='failed',
                error_message=str(exc)
            )
            logger.exception("Failed to send WhatsApp notification")
            # we do not retry WhatsApp separately


@shared_task
def check_milestones_and_notify():
    """
    Checks container booking volume against milestones and emails admin when each is reached.
    """
    total_volume = Booking.total_booked_volume()
    for fraction in MILESTONES:
        threshold = (CONTAINER_CAPACITY * fraction).quantize(Decimal('0.01'))
        # fire when crossing the threshold (±0.01 tolerance)
        if threshold - Decimal('0.01') < total_volume <= threshold + Decimal('0.01'):
            pct = int(fraction * 100)
            subject = f"{pct}% Container Booked"
            message = (
                f"{total_volume:.2f}m³ of {CONTAINER_CAPACITY}m³ "
                f"container capacity reached ({pct}%)."
            )
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=True,
            )
            # Log to NotificationLog if you want (optional)
            NotificationLog.objects.create(
                booking=None,
                channel='email',
                recipient=settings.ADMIN_EMAIL,
                payload=message,
                status='success'
            )


@shared_task
def notify_dispatch_ready():
    """
    Notifies admin (email + WhatsApp) when container is fully booked.
    """
    total_volume = Booking.total_booked_volume()
    if total_volume >= CONTAINER_CAPACITY:
        subject = "Container Ready to Dispatch"
        message = f"All {CONTAINER_CAPACITY}m³ booked—container is ready to dispatch!"
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            fail_silently=True,
        )
        NotificationLog.objects.create(
            booking=None,
            channel='email',
            recipient=settings.ADMIN_EMAIL,
            payload=message,
            status='success'
        )

        # WhatsApp alert to admin if configured
        if all([
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN,
            settings.ADMIN_WHATSAPP
        ]):
            try:
                tw_client = TwilioClient(
                    settings.TWILIO_ACCOUNT_SID,
                    settings.TWILIO_AUTH_TOKEN
                )
                wa_body = 'Container filled—ready to dispatch!'
                tw_client.messages.create(
                    body=wa_body,
                    from_=f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
                    to=f"whatsapp:{settings.ADMIN_WHATSAPP}"
                )
                NotificationLog.objects.create(
                    booking=None,
                    channel='whatsapp',
                    recipient=settings.ADMIN_WHATSAPP,
                    payload=wa_body,
                    status='success'
                )
            except Exception as exc:
                NotificationLog.objects.create(
                    booking=None,
                    channel='whatsapp',
                    recipient=settings.ADMIN_WHATSAPP,
                    payload=wa_body,
                    status='failed',
                    error_message=str(exc)
                )
                logger.exception("Failed to send dispatch-ready WhatsApp")











# import os
# from decimal import Decimal
# from celery import shared_task
# from django.core.mail import send_mail

# # env variables
# ADMIN_EMAIL    = os.getenv('ADMIN_EMAIL')
# TWILIO_SID     = os.getenv('TWILIO_SID')
# TWILIO_TOKEN   = os.getenv('TWILIO_TOKEN')
# TWILIO_FROM    = os.getenv('TWILIO_FROM')
# ADMIN_WHATSAPP = os.getenv('ADMIN_WHATSAPP')

# MILESTONES = [Decimal('0.25'), Decimal('0.50'), Decimal('0.75')]
# CONTAINER_CAPACITY = Decimal('66.16')

# @shared_task
# def send_booking_notifications(booking_id):
#     # import inside to avoid circular import
#     from .models import Booking
#     b = Booking.objects.get(pk=booking_id)

#     # send email
#     recipient = b.user.email if b.user and b.user.email else ADMIN_EMAIL
#     send_mail(
#         subject=f'Booking Confirmed: {b.reference_code}',
#         message=(
#             f'Your booking {b.reference_code} is confirmed.\n'
#             f'Box: {b.box_type.name}\n'
#             f'Pickup: {b.pickup_date} ({b.pickup_slot})\n'
#             f'Cost: GHS {b.cost}'
#         ),
#         from_email='no-reply@cargoghana.com',
#         recipient_list=[recipient],
#     )

#     # optional WhatsApp
#     try:
#         from twilio.rest import Client
#     except ImportError:
#         Client = None

#     if Client and TWILIO_SID and TWILIO_TOKEN and ADMIN_WHATSAPP:
#         client = Client(TWILIO_SID, TWILIO_TOKEN)
#         client.messages.create(
#             body=(
#                 f'New booking {b.reference_code}: '
#                 f'{b.box_type.name}, {b.weight_kg}kg, GHS {b.cost}'
#             ),
#             from_=f'whatsapp:{TWILIO_FROM}',
#             to=f'whatsapp:{ADMIN_WHATSAPP}',
#         )

# @shared_task
# def check_milestones_and_notify():
#     from .models import Booking
#     total = Booking.total_booked_volume()
#     for m in MILESTONES:
#         threshold = (CONTAINER_CAPACITY * m).quantize(Decimal('0.01'))
#         if threshold - Decimal('0.01') < total <= threshold + Decimal('0.01'):
#             pct = int(m * 100)
#             send_mail(
#                 subject=f'{pct}% Container Booked',
#                 message=f'{total:.2f}m³ of {CONTAINER_CAPACITY}m³ reached ({pct}%).',
#                 from_email='no-reply@cargoghana.com',
#                 recipient_list=[ADMIN_EMAIL],
#             )

# @shared_task
# def notify_dispatch_ready():
#     from .models import Booking
#     total = Booking.total_booked_volume()
#     if total >= CONTAINER_CAPACITY:
#         send_mail(
#             subject='Container Ready to Dispatch',
#             message=f'All {CONTAINER_CAPACITY}m³ booked—ready to dispatch!',
#             from_email='no-reply@cargoghana.com',
#             recipient_list=[ADMIN_EMAIL],
#         )
#         try:
#             from twilio.rest import Client
#         except ImportError:
#             Client = None

#         if Client and TWILIO_SID and TWILIO_TOKEN and ADMIN_WHATSAPP:
#             client = Client(TWILIO_SID, TWILIO_TOKEN)
#             client.messages.create(
#                 body='Container filled—ready to dispatch!',
#                 from_=f'whatsapp:{TWILIO_FROM}',
#                 to=f'whatsapp:{ADMIN_WHATSAPP}',
#             )
