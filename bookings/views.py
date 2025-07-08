from decimal import Decimal
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import BoxType, Booking
from .serializers import (
    BoxTypeSerializer, BookingSerializer, ContainerProgressSerializer
)

class BoxTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BoxType.objects.all()
    serializer_class = BoxTypeSerializer
    permission_classes = [AllowAny]

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all().order_by('-created_at')
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    http_method_names = ['get', 'post', 'retrieve']

class ContainerProgressView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        total = Booking.total_booked_volume()
        goal = Decimal('66.16')
        percent = (total / goal * 100) if goal > 0 else Decimal(0)
        data = {
            'total_volume': round(total, 2),
            'goal_volume': goal,
            'percent': min(round(percent, 2), Decimal(100))
        }
        return Response(ContainerProgressSerializer(data).data)
