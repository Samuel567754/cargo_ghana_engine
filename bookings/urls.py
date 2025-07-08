from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BoxTypeViewSet, BookingViewSet, ContainerProgressView, VolumeCalcAPIView, mark_ready_batches_api, check_dispatch_api,    BookingTrackingView    

router = DefaultRouter()
router.register(r'boxes', BoxTypeViewSet, basename='boxes')
router.register(r'bookings', BookingViewSet, basename='bookings')

urlpatterns = [
    path('', include(router.urls)),
    path('container-progress/', ContainerProgressView.as_view(), name='container-progress'),
    path('volume-calc/', VolumeCalcAPIView.as_view(), name='volume-calc'),
    path('admin/mark-ready-batches/', mark_ready_batches_api, name='mark-ready-batches'),
     path(
        'admin/check-dispatch/',
        check_dispatch_api,
        name='admin-check-dispatch'
    ),
    path('track/<str:reference_code>/', BookingTrackingView.as_view(), name='booking-track'),
]
