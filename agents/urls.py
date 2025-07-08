from rest_framework.routers import DefaultRouter
from .views import AgentApplicationViewSet

router = DefaultRouter()
router.register(r'', AgentApplicationViewSet, basename='agents')

urlpatterns = router.urls
