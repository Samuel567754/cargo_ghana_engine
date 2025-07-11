from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.utils import timezone
from .models import Referral
from .serializers import ReferralSerializer

class ReferralViewSet(viewsets.ModelViewSet):
    queryset = Referral.objects.all().order_by('-created_at')
    serializer_class = ReferralSerializer
    http_method_names = ['get', 'post', 'patch']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'statistics']:
            return [IsAdminUser()]
        return [AllowAny()]

    @action(detail=True, methods=['get'])
    def track_click(self, request, pk=None):
        referral = self.get_object()
        referral.track_click()
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def statistics(self, request):
        total_referrals = Referral.objects.count()
        total_successful = sum(r.successful_referrals for r in Referral.objects.all())
        total_clicks = sum(r.link_clicks for r in Referral.objects.all())
        total_rewards = sum(r.total_reward_earned for r in Referral.objects.all())

        return Response({
            'total_referrals': total_referrals,
            'total_successful_referrals': total_successful,
            'total_clicks': total_clicks,
            'total_rewards_earned': total_rewards,
            'conversion_rate': round((total_successful / total_referrals * 100), 2) if total_referrals > 0 else 0
        })
