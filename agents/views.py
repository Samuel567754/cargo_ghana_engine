from rest_framework import viewsets
from .models import AgentApplication
from .serializers import AgentApplicationSerializer
from rest_framework.permissions import AllowAny, IsAdminUser

class AgentApplicationViewSet(viewsets.ModelViewSet):
    queryset = AgentApplication.objects.all().order_by('-submitted_at')
    serializer_class = AgentApplicationSerializer
    http_method_names = ['get', 'post']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAdminUser()]  # Only staff can view applications
        return [AllowAny()]  # Public can apply
