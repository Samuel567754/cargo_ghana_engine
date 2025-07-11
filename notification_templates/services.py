from django.template import Template, Context
from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client
from .models import NotificationTemplate
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.twilio_client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )

    def render_template(self, template_name, context):
        try:
            template = NotificationTemplate.objects.get(
                name=template_name,
                is_active=True
            )
            template_context = Context(context or {})
            body = Template(template.body).render(template_context)
            subject = None
            if template.subject:
                subject = Template(template.subject).render(template_context)
            return template.channel, subject, body
        except NotificationTemplate.DoesNotExist:
            logger.error(f'Template not found: {template_name}')
            raise

    def send_notification(self, template_name, recipient, context=None):
        try:
            channel, subject, body = self.render_template(template_name, context)
            if channel == 'email':
                return self.send_email(recipient, subject, body)
            elif channel == 'whatsapp':
                return self.send_whatsapp(recipient, body)
        except Exception as e:
            logger.error(f'Failed to send {template_name} to {recipient}: {str(e)}')
            raise

    def send_email(self, to_email, subject, body):
        return send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email]
        )

    def send_whatsapp(self, to_number, body):
        return self.twilio_client.messages.create(
            body=body,
            from_=f'whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}',
            to=f'whatsapp:{to_number}'
        )