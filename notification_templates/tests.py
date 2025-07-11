import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.template import Template, Context
from .models import NotificationTemplate
from .services import NotificationService

pytestmark = pytest.mark.django_db

class NotificationTemplateTests(TestCase):
    def test_create_email_template(self):
        template = NotificationTemplate.objects.create(
            name="Test Email",
            channel="email",
            subject="Test Subject",
            body="Hello {name}"
        )
        self.assertEqual(str(template), "Test Email (email)")

    def test_email_template_requires_subject(self):
        with self.assertRaises(ValidationError):
            template = NotificationTemplate(
                name="Invalid Email",
                channel="email",
                body="Hello {name}"
            )
            template.clean()

    def test_whatsapp_template_without_subject(self):
        template = NotificationTemplate.objects.create(
            name="Test WhatsApp",
            channel="whatsapp",
            body="Hello {name}"
        )
        template.clean()  # Should not raise ValidationError

    def test_template_with_invalid_channel(self):
        with self.assertRaises(ValidationError):
            NotificationTemplate.objects.create(
                name="Invalid Channel",
                channel="invalid",
                body="Test body"
            )
    
    def test_template_ordering(self):
        NotificationTemplate.objects.create(
            name="Z Template",
            channel="email",
            subject="Test",
            body="Test"
        )
        NotificationTemplate.objects.create(
            name="A Template",
            channel="email",
            subject="Test",
            body="Test"
        )
        
        templates = NotificationTemplate.objects.all()
        self.assertEqual(templates[0].name, "A Template")
        self.assertEqual(templates[1].name, "Z Template")

    def test_template_rendering(self):
        template = NotificationTemplate.objects.create(
            name="test_template",
            channel="email",
            subject="Hello {{name}}",
            body="Welcome {{name}}!"
        )
        service = NotificationService()
        channel, subject, body = service.render_template(
            "test_template", 
            {"name": "John"}
        )
        self.assertEqual(channel, "email")
        self.assertEqual(subject, "Hello John")
        self.assertEqual(body, "Welcome John!")

    def test_inactive_template(self):
        template = NotificationTemplate.objects.create(
            name="inactive_template",
            channel="email",
            subject="Test",
            body="Test",
            is_active=False
        )
        service = NotificationService()
        with self.assertRaises(NotificationTemplate.DoesNotExist):
            service.render_template("inactive_template", {})
