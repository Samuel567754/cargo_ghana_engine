from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationTemplateViewSet

router = DefaultRouter()
router.register('templates', NotificationTemplateViewSet)

urlpatterns = [
    path('', include(router.urls)),
]