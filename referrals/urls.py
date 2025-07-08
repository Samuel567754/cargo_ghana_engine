from rest_framework.routers import DefaultRouter
from .views import ReferralViewSet

router = DefaultRouter()
router.register(r'', ReferralViewSet, basename='referrals')

urlpatterns = router.urls
