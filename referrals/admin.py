from django.contrib import admin
from .models import Referral

@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('code','email','reward_amount','created_at')
    readonly_fields = ('code','reward_amount','created_at')
    search_fields = ('code','email')
