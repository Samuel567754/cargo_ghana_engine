from rest_framework import serializers
from .models import Referral

class ReferralSerializer(serializers.ModelSerializer):
    shareable_link = serializers.SerializerMethodField()
    conversion_rate = serializers.SerializerMethodField()

    class Meta:
        model = Referral
        fields = [
            'id', 'email', 'code', 'created_at',
            'total_referrals', 'successful_referrals',
            'link_clicks', 'last_clicked_at',
            'reward_amount', 'reward_status',
            'total_reward_earned', 'shareable_link',
            'conversion_rate'
        ]
        read_only_fields = [
            'id', 'code', 'total_referrals',
            'successful_referrals', 'link_clicks',
            'last_clicked_at', 'reward_amount',
            'reward_status', 'total_reward_earned',
            'shareable_link', 'conversion_rate'
        ]

    def get_shareable_link(self, obj):
        return obj.get_shareable_link()

    def get_conversion_rate(self, obj):
        if obj.total_referrals > 0:
            return round((obj.successful_referrals / obj.total_referrals) * 100, 2)
        return 0.0
