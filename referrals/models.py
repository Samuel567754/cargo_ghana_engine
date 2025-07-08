from django.db import models
from django.conf import settings
import uuid

class Referral(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField()
    code = models.CharField(max_length=12, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # e.g. reward can be stored or calculated
    reward_amount = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    def __str__(self):
        return self.code
