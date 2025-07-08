from decimal import Decimal
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAdminUser,IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import status
from .serializers import VolumeCalcSerializer
from rest_framework.decorators import api_view, permission_classes
from .models import ContainerBatch
from django.core import management


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



class VolumeCalcAPIView(APIView):
    permission_classes = [AllowAny]                  # ← allow unauthenticated
    """
    POST /api/volume-calc/
    {
        "boxes": [
            { "type_id": 1, "quantity": 3 },
            { "type_id": 2, "quantity": 5 }
        ]
    }
    Response:
    {
        "total_volume": 4.56,
        "total_cost": "1234.00"
    }
    """
    def post(self, request, *args, **kwargs):
        serializer = VolumeCalcSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)



@api_view(['POST'])
@permission_classes([IsAdminUser])
def mark_ready_batches_api(request):
    """
    POST /api/admin/mark-ready-batches/
    Triggers the same logic as the management command.
    """
    out = []
    # Capture command output
    class Collector:
        def write(self, msg): out.append(msg)
    management.call_command(
        'mark_ready_batches',
        stdout=Collector(),
        stderr=Collector()
    )
    return Response({'detail': out}, status=status.HTTP_200_OK)




@api_view(['GET'])
@permission_classes([IsAdminUser])
def check_dispatch_api(request):
    """
    GET /api/admin/check-dispatch/
    Runs the `check_dispatch` command and returns its output.
    """
    output_lines = []
    class Collector:
        def write(self, msg):
            # strip trailing newlines for cleanliness
            output_lines.append(msg.rstrip())

    management.call_command(
        'check_dispatch',
        stdout=Collector(),
        stderr=Collector()
    )
    return Response(
        {'output': output_lines},
        status=status.HTTP_200_OK
    )