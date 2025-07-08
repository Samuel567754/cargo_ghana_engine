from rest_framework import serializers
from .models import Referral
import uuid

class ReferralSerializer(serializers.ModelSerializer):
    class Meta:
        model = Referral
        fields = ['id', 'email', 'code', 'reward_amount', 'created_at']
        read_only_fields = ['id', 'code', 'reward_amount', 'created_at']

    def create(self, validated_data):
        validated_data['code'] = uuid.uuid4().hex[:12].upper()
        # you may calculate reward here
        validated_data['reward_amount'] = 10.00
        return super().create(validated_data)
