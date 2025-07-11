from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.crypto import get_random_string
import uuid

class Referral(models.Model):
    REWARD_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField()
    code = models.CharField(max_length=12, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Referral tracking fields
    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='referrals_made'
    )
    total_referrals = models.PositiveIntegerField(default=0)
    successful_referrals = models.PositiveIntegerField(default=0)
    link_clicks = models.PositiveIntegerField(default=0)
    last_clicked_at = models.DateTimeField(null=True, blank=True)
    
    # Reward tracking fields
    reward_amount = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    reward_status = models.CharField(
        max_length=20,
        choices=REWARD_STATUS_CHOICES,
        default='pending'
    )
    reward_updated_at = models.DateTimeField(auto_now=True)
    total_reward_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['email']),
            models.Index(fields=['reward_status'])
        ]

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_referral_code()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_referral_code():
        return get_random_string(12, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')

    def get_absolute_url(self):
        return reverse('referral-landing', kwargs={'code': self.code})

    def get_shareable_link(self):
        return f"{settings.SITE_URL}{self.get_absolute_url()}"

    def track_click(self):
        self.link_clicks += 1
        self.last_clicked_at = models.functions.Now()
        self.save(update_fields=['link_clicks', 'last_clicked_at'])

    def track_successful_referral(self, booking):
        self.successful_referrals += 1
        self.total_referrals += 1
        # Calculate reward based on booking amount
        reward = self.calculate_reward(booking)
        self.reward_amount += reward
        self.total_reward_earned += reward
        self.save()

    def calculate_reward(self, booking):
        # Basic reward calculation - can be enhanced based on business rules
        base_reward = 10.00  # Base reward for each successful referral
        booking_percentage = 0.05  # 5% of booking cost
        booking_reward = float(booking.cost) * booking_percentage
        return base_reward + booking_reward
