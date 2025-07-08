from rest_framework import viewsets
from .models import TrackingRecord
from .serializers import TrackingRecordSerializer
from rest_framework.permissions import AllowAny

class TrackingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TrackingRecord.objects.all().order_by('timestamp')
    serializer_class = TrackingRecordSerializer
    permission_classes = [AllowAny]
