from rest_framework import viewsets
from .models import Referral
from .serializers import ReferralSerializer
from rest_framework.permissions import AllowAny, IsAdminUser

class ReferralViewSet(viewsets.ModelViewSet):
    queryset = Referral.objects.all().order_by('-created_at')
    serializer_class = ReferralSerializer
    http_method_names = ['get', 'post']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAdminUser()]  # Only staff can view
        return [AllowAny()]  # Anyone can submit
