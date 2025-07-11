from decimal import Decimal
from django.core import management
from rest_framework import viewsets, status, generics
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from django.http import FileResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .pdf_generator import generate_box_cheatsheet

from .models import BoxType, Booking, send_booking_notifications
from .serializers import (
    BoxTypeSerializer,
    VolumeCalcSerializer,
    ContainerProgressSerializer,
    BookingCreateSerializer,
    BookingDetailSerializer,
    BookingTrackingSerializer,
)


class BoxTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset         = BoxType.objects.all()
    serializer_class = BoxTypeSerializer
    permission_classes = [AllowAny]


class BookingViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Booking.objects.select_related(
            'user',
            'box_type',
            'referral'
        ).prefetch_related(
            'tracking',
            'notifications'
        )
    queryset = Booking.objects.all().order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return BookingCreateSerializer
        return BookingDetailSerializer

    def get_permissions(self):
        if self.action in ['create']:
            return [AllowAny()]
        return [IsAdminUser()]

    def perform_create(self, serializer):
        booking = serializer.save()
        # task is already enqueued in model.save()
        # nothing more to do here


class ContainerProgressView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        total   = Booking.total_booked_volume()
        goal    = Decimal('66.16')
        percent = (total / goal * 100) if goal > 0 else Decimal('0')
        data = {
            'total_volume': total.quantize(Decimal('0.01')),
            'goal_volume':  goal.quantize(Decimal('0.01')),
            'percent':      min(percent.quantize(Decimal('0.01')), Decimal('100.00')),
        }
        serializer = ContainerProgressSerializer(data)
        return Response(serializer.data)


class VolumeCalcAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = VolumeCalcSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.save(), status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def mark_ready_batches_api(request):
    out = []
    class Collector:
        def write(self, msg): out.append(msg)
    management.call_command('mark_ready_batches', stdout=Collector(), stderr=Collector())
    return Response({'detail': out})


@api_view(['GET'])
@permission_classes([IsAdminUser])
def check_dispatch_api(request):
    out = []
    class Collector:
        def write(self, msg): out.append(msg.rstrip())
    management.call_command('check_dispatch', stdout=Collector(), stderr=Collector())
    return Response({'output': out})


class BookingTrackingView(generics.RetrieveAPIView):
    queryset         = Booking.objects.all()
    serializer_class = BookingTrackingSerializer
    lookup_field     = 'reference_code'
    permission_classes = [AllowAny]


class ContainerCapacityView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        current_batch = ContainerBatch.objects.filter(status='open').first()
        if not current_batch:
            return Response({
                'error': 'No open container batch found'
            }, status=status.HTTP_404_NOT_FOUND)

        latest_capacity = ContainerCapacity.objects.filter(batch=current_batch).first()
        if not latest_capacity:
            latest_capacity = ContainerCapacity.log_capacity(current_batch)

        serializer = ContainerCapacitySerializer(latest_capacity)
        return Response(serializer.data)


class CapacityHistoryView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        days = int(request.GET.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        
        capacity_logs = ContainerCapacity.objects.filter(
            timestamp__gte=start_date
        ).order_by('timestamp')

        serializer = ContainerCapacitySerializer(capacity_logs, many=True)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def download_box_cheatsheet(request):
    pdf_buffer = generate_box_cheatsheet()
    return FileResponse(
        pdf_buffer,
        as_attachment=True,
        filename='box_volume_cheatsheet.pdf',
        content_type='application/pdf'
    )
