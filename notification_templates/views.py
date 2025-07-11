from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from .models import NotificationTemplate
from .serializers import NotificationTemplateSerializer

class NotificationTemplateViewSet(viewsets.ModelViewSet):
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAdminUser]

# Create your views here.
