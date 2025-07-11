from rest_framework.routers import DefaultRouter
from .views import AgentApplicationViewSet

router = DefaultRouter()
router.register('applications', AgentApplicationViewSet, basename='agent-applications')

urlpatterns = router.urls
