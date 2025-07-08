from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BoxTypeViewSet, BookingViewSet, ContainerProgressView

router = DefaultRouter()
router.register(r'boxes', BoxTypeViewSet, basename='boxes')
router.register(r'bookings', BookingViewSet, basename='bookings')

urlpatterns = [
    path('', include(router.urls)),
    path('container-progress/', ContainerProgressView.as_view(), name='container-progress'),
]
