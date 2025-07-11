import os
from decimal import Decimal
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.mail import send_mail
from twilio.rest import Client as TwilioClient

from .models import Booking, NotificationLog, ContainerBatch
from django.template.loader import render_to_string
from django.utils import timezone
from notification_templates.services import NotificationService

logger = get_task_logger(__name__)

# Milestone thresholds (fractions of total capacity)
MILESTONES = [
    Decimal('0.25'),
    Decimal('0.50'),
    Decimal('0.75'),
]
CONTAINER_CAPACITY = Decimal('66.16')


from notification_templates.services import NotificationService

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_booking_notifications(self, booking_id):
    try:
        booking = Booking.objects.select_related(
            'user',
            'box_type',
            'referral'
        ).get(id=booking_id)
    except Booking.DoesNotExist as exc:
        logger.error(f'Booking {booking_id} not found: {exc}')
        return

    notification_service = NotificationService()
    context = {
        'user_name': booking.user.get_full_name() or booking.user.username,
        'reference_code': booking.reference_code,
        'pickup_date': booking.pickup_date.strftime('%Y-%m-%d'),
        'pickup_slot': booking.pickup_slot,
        'box_type': str(booking.box_type),
        'quantity': booking.quantity,
        'tracking_url': f'{settings.FRONTEND_URL}/track/{booking.reference_code}'
    }

    try:
        # Send email notification
        notification_service.send_notification(
            'booking_confirmation_email',
            booking.user.email,
            context
        )
        NotificationLog.objects.create(
            booking=booking,
            channel='email',
            recipient=booking.user.email,
            status='success',
            payload=str(context)
        )

        # Send WhatsApp notification if phone number exists
        if booking.user.phone:
            notification_service.send_notification(
                'booking_confirmation_whatsapp',
                booking.user.phone,
                context
            )
            NotificationLog.objects.create(
                booking=booking,
                channel='whatsapp',
                recipient=booking.user.phone,
                status='success',
                payload=str(context)
            )

    except Exception as exc:
        NotificationLog.objects.create(
            booking=booking,
            channel='email',
            recipient=booking.user.email,
            status='failed',
            error_message=str(exc),
            payload=str(context)
        )
        raise self.retry(exc=exc)


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


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification(self, recipient, template_name, context=None, channel='email'):
    notification_service = NotificationService()
    try:
        notification_service.send_notification(
            recipient=recipient,
            template_name=template_name,
            context=context,
            channel=channel
        )
        NotificationLog.objects.create(
            channel=channel,
            recipient=recipient,
            payload=str(context),
            status='success'
        )
    except Exception as exc:
        NotificationLog.objects.create(
            channel=channel,
            recipient=recipient,
            payload=str(context),
            status='failed',
            error_message=str(exc)
        )
        raise self.retry(exc=exc)
