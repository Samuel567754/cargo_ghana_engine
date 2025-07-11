from rest_framework import serializers
from .models import NotificationTemplate

class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')