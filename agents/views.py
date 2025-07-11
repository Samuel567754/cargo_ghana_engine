from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.utils import timezone
from .models import AgentApplication
from .serializers import AgentApplicationSerializer, AdminAgentApplicationSerializer

class AgentApplicationViewSet(viewsets.ModelViewSet):
    queryset = AgentApplication.objects.all().order_by('-submitted_at')
    http_method_names = ['get', 'post', 'patch']

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return AdminAgentApplicationSerializer
        return AgentApplicationSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'update', 'partial_update', 'approve', 'reject']:
            return [IsAdminUser()]
        return [AllowAny()]

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        application = self.get_object()
        application.status = 'approved'
        application.reviewed_at = timezone.now()
        application.reviewed_by = request.user
        application.admin_notes = request.data.get('notes', '')
        application.save()
        return Response(self.get_serializer(application).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject(self, request, pk=None):
        application = self.get_object()
        application.status = 'rejected'
        application.reviewed_at = timezone.now()
        application.reviewed_by = request.user
        application.admin_notes = request.data.get('notes', '')
        application.save()
        return Response(self.get_serializer(application).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def review(self, request, pk=None):
        application = self.get_object()
        application.status = 'under_review'
        application.save()
        return Response(self.get_serializer(application).data)
