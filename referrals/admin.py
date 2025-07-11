from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from .models import Referral

class ReferralResource(resources.ModelResource):
    class Meta:
        model = Referral
        fields = ('id', 'code', 'email', 'referrer__email', 'total_referrals', 
                 'successful_referrals', 'link_clicks', 'reward_status', 
                 'total_reward_earned', 'created_at')

@admin.register(Referral)
class ReferralAdmin(ImportExportModelAdmin):
    resource_class = ReferralResource
    list_display = (
        'code', 'email', 'referrer',
        'total_referrals', 'successful_referrals',
        'link_clicks', 'reward_status',
        'total_reward_earned', 'created_at'
    )
    list_filter = ('reward_status', 'created_at')
    readonly_fields = (
        'code', 'total_referrals',
        'successful_referrals', 'link_clicks',
        'last_clicked_at', 'total_reward_earned'
    )
    search_fields = ('code', 'email', 'referrer__email')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Basic Information', {
            'fields': ('email', 'code', 'referrer')
        }),
        ('Tracking Statistics', {
            'fields': (
                'total_referrals', 'successful_referrals',
                'link_clicks', 'last_clicked_at'
            )
        }),
        ('Reward Information', {
            'fields': (
                'reward_amount', 'reward_status',
                'total_reward_earned'  # Removed reward_updated_at
            )
        })
    )
