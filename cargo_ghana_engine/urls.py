from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
     # JWT login/logout
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),   # login
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),  # logout
    # your app APIs
    path('api/accounts/', include('accounts.urls')),
    path('api/bookings/', include('bookings.urls')),
    path('api/tracking/', include('tracking.urls')),
    path('api/referrals/', include('referrals.urls')),
    path('api/agents/', include('agents.urls')),
    path('api/core/', include('core.urls')),  # for API versioning and future expansion
    path('api/notifications/', include('notification_templates.urls')),
]
