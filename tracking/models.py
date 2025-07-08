from django.db import models
import uuid
from django.conf import settings

class TrackingRecord(models.Model):
    booking = models.ForeignKey('bookings.Booking', on_delete=models.CASCADE, related_name='tracking')
    status = models.CharField(max_length=50)  # e.g. 'In Transit', 'Delivered'
    location = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.booking.id} - {self.status}'
