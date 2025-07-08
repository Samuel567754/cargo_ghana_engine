from rest_framework import serializers
from .models import AgentApplication

class AgentApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentApplication
        fields = '__all__'
        read_only_fields = ['id', 'submitted_at', 'approved']
