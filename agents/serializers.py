from rest_framework import serializers
from .models import AgentApplication

class AgentApplicationSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = AgentApplication
        fields = [
            'id', 'name', 'email', 'phone', 'company', 'experience',
            'id_document', 'business_license', 'resume',
            'status', 'status_display', 'submitted_at',
            'reviewed_at', 'reviewed_by', 'admin_notes'
        ]
        read_only_fields = [
            'id', 'submitted_at', 'status', 'reviewed_at',
            'reviewed_by', 'admin_notes', 'status_display'
        ]

    def validate(self, data):
        # Ensure required documents are provided
        if self.context['request'].method == 'POST':
            if not data.get('id_document'):
                raise serializers.ValidationError({'id_document': 'This document is required.'})
            if not data.get('resume'):
                raise serializers.ValidationError({'resume': 'Resume/CV is required.'})
        return data

class AdminAgentApplicationSerializer(AgentApplicationSerializer):
    class Meta(AgentApplicationSerializer.Meta):
        read_only_fields = ['id', 'submitted_at']
