from rest_framework.routers import DefaultRouter
from .views import UserViewSet

router = DefaultRouter()
# register and me are under this ViewSet
router.register(r'', UserViewSet, basename='users')

urlpatterns = router.urls
