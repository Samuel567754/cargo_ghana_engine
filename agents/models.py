from django.db import models
from django.core.validators import FileExtensionValidator
from django.conf import settings
import uuid

class AgentApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    company = models.CharField(max_length=100, blank=True)
    experience = models.TextField(blank=True)
    
    # Document fields - made nullable for existing records
    id_document = models.FileField(
        upload_to='agent_documents/id/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        help_text='Valid ID document (PDF, JPG, JPEG, PNG)',
        null=True,  # Added for existing records
        blank=True  # Added for form validation
    )
    business_license = models.FileField(
        upload_to='agent_documents/license/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        help_text='Business license or registration (PDF, JPG, JPEG, PNG)',
        null=True,
        blank=True
    )
    resume = models.FileField(
        upload_to='agent_documents/resume/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])],
        help_text='Resume or CV (PDF, DOC, DOCX)',
        null=True,  # Added for existing records
        blank=True  # Added for form validation
    )
    
    # Application status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications'
    )
    admin_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f'{self.name} ({self.email}) - {self.get_status_display()}'

    def clean(self):
        from django.core.exceptions import ValidationError
        # Ensure documents are provided for new applications
        if not self.pk:  # Only for new records
            if not self.id_document:
                raise ValidationError({'id_document': 'ID document is required for new applications.'})
            if not self.resume:
                raise ValidationError({'resume': 'Resume/CV is required for new applications.'})
