import os
from decimal import Decimal
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.mail import send_mail
from twilio.rest import Client as TwilioClient

from .models import Booking, NotificationLog, ContainerBatch

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
        booking = Booking.objects.select_related('user').get(id=booking_id)
    except Booking.DoesNotExist as exc:
        logger.error(f'Booking {booking_id} not found: {exc}')
        return

    # 1) EMAIL
    if booking.user and booking.user.email:
        subject = f"Booking Confirmed: {booking.reference_code}"
        body = (
            f"Hello {booking.user.get_full_name() or booking.user.username},\n\n"
            f"Your booking {booking.reference_code} has been received.\n"
            f"Pickup: {booking.pickup_date} at {booking.pickup_slot}\n"
            f"Total Cost: GHS {booking.cost}\n\nThank you!"
        )
        try:
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [booking.user.email],
                fail_silently=False,
            )
            NotificationLog.objects.create(
                booking=booking,
                channel='email',
                recipient=booking.user.email,
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
    else:
        logger.info(f"Booking {booking_id} has no user email; skipping email notification")

    # 2) WHATSAPP
    wa_number = getattr(getattr(booking.user, 'profile', None), 'whatsapp_number', None)
    if wa_number:
        wa_body = (
            f"Booking {booking.reference_code} is confirmed!\n"
            f"Pickup: {booking.pickup_date} @ {booking.pickup_slot}\n"
            f"Cost: GHS {booking.cost}"
        )
        try:
            tw_client = TwilioClient(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
            tw_client.messages.create(
                body=wa_body,
                from_=f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
                to=f"whatsapp:{wa_number}"
            )
            NotificationLog.objects.create(
                booking=booking,
                channel='whatsapp',
                recipient=wa_number,
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
    else:
        logger.info(f"Booking {booking_id} user has no WhatsApp number; skipping WhatsApp notification")


@shared_task
def check_milestones_and_notify():
    """
    Checks container booking volume against milestones and emails admin when each is reached.
    """
    total_volume = Booking.total_booked_volume()
    for fraction in MILESTONES:
        threshold = (CONTAINER_CAPACITY * fraction).quantize(Decimal('0.01'))
        if threshold - Decimal('0.01') < total_volume <= threshold + Decimal('0.01'):
            pct = int(fraction * 100)
            subject = f"{pct}% Container Booked"
            message = (
                f"{total_volume:.2f}m³ of {CONTAINER_CAPACITY}m³ "
                f"container capacity reached ({pct}%)."
            )
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.ADMIN_EMAIL],
                    fail_silently=False,
                )
                NotificationLog.objects.create(
                    booking=None,
                    channel='email',
                    recipient=settings.ADMIN_EMAIL,
                    payload=message,
                    status='success'
                )
            except Exception as exc:
                logger.exception("Failed to notify milestone")


@shared_task
def notify_dispatch_ready():
    """
    Notifies admin (email + WhatsApp) when container is fully booked.
    """
    total_volume = Booking.total_booked_volume()
    if total_volume >= CONTAINER_CAPACITY:
        subject = "Container Ready to Dispatch"
        message = f"All {CONTAINER_CAPACITY}m³ booked—container is ready to dispatch!"
        # Email
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=False,
            )
            NotificationLog.objects.create(
                booking=None,
                channel='email',
                recipient=settings.ADMIN_EMAIL,
                payload=message,
                status='success'
            )
        except Exception:
            logger.exception("Failed to send dispatch-ready email")

        # WhatsApp to admin
        admin_wa = getattr(settings, 'ADMIN_WHATSAPP', None)
        if all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, admin_wa]):
            try:
                tw_client = TwilioClient(
                    settings.TWILIO_ACCOUNT_SID,
                    settings.TWILIO_AUTH_TOKEN
                )
                wa_body = 'Container filled—ready to dispatch!'
                tw_client.messages.create(
                    body=wa_body,
                    from_=f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
                    to=f"whatsapp:{admin_wa}"
                )
                NotificationLog.objects.create(
                    booking=None,
                    channel='whatsapp',
                    recipient=admin_wa,
                    payload=wa_body,
                    status='success'
                )
            except Exception:
                logger.exception("Failed to send dispatch-ready WhatsApp")


@shared_task
def check_and_mark_batches():
    """
    1) Checks total booked volume.
    2) Ensures there's a single 'open' ContainerBatch.
    3) If capacity reached, marks batch ready + fires notify_dispatch_ready.
    """
    total = Booking.total_booked_volume()

    batch, created = ContainerBatch.objects.get_or_create(
        status='open',
        defaults={'target_volume': CONTAINER_CAPACITY}
    )

    # If threshold reached
    if total >= CONTAINER_CAPACITY and batch.status != 'ready':
        batch.status = 'ready'
        batch.save()
        logger.info(f"ContainerBatch {batch.id} marked READY at {total} m³")
        notify_dispatch_ready.delay()
