from django.db import models
from django.core.exceptions import ValidationError

class NotificationTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField(help_text='Use {{variable}} for template variables')
    channel = models.CharField(
        max_length=20,
        choices=[('email', 'Email'), ('whatsapp', 'WhatsApp')],
        default='email'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.channel == 'email' and not self.subject:
            raise ValidationError({'subject': 'Subject is required for email templates'})

    def __str__(self):
        return f'{self.name} ({self.get_channel_display()})'

    class Meta:
        ordering = ['name']
# Create your models here.
