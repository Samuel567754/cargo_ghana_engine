from decimal import Decimal
from rest_framework import serializers
from .models import BoxType, Booking
from referrals.models import Referral


class ContainerProgressSerializer(serializers.Serializer):
    total_volume = serializers.DecimalField(max_digits=10, decimal_places=2)
    goal_volume  = serializers.DecimalField(max_digits=10, decimal_places=2)
    percent      = serializers.DecimalField(max_digits=5, decimal_places=2)


class BoxTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = BoxType
        fields = '__all__'


class VolumeCalcItemSerializer(serializers.Serializer):
    type_id  = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class VolumeCalcSerializer(serializers.Serializer):
    boxes = serializers.ListSerializer(child=VolumeCalcItemSerializer(), allow_empty=False)
    total_volume = serializers.FloatField(read_only=True)
    total_cost   = serializers.CharField(read_only=True)  # return as string

    def validate(self, data):
        ids = [i['type_id'] for i in data['boxes']]
        existing = set(BoxType.objects.filter(id__in=ids).values_list('id', flat=True))
        missing = set(ids) - existing
        if missing:
            raise serializers.ValidationError(f"BoxType(s) not found: {missing}")
        return data

    def create(self, validated_data):
        total_vol = Decimal('0')
        for item in validated_data['boxes']:
            bt  = BoxType.objects.get(id=item['type_id'])
            qty = item['quantity']
            total_vol += bt.volume_m3 * qty

        total_cost = (total_vol * Decimal("453.66")).quantize(Decimal('0.01'))
        return {
            'total_volume': float(total_vol.quantize(Decimal('0.01'))),
            'total_cost':   str(total_cost)
        }


class BookingCreateSerializer(serializers.ModelSerializer):
    id            = serializers.UUIDField(read_only=True)
    quantity      = serializers.IntegerField(min_value=1)
    referral_code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    cost          = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model  = Booking
        fields = [
            'id',
            'box_type',
            'quantity',
            'pickup_address',
            'pickup_date',
            'pickup_slot',
            'referral_code',
            'cost',
        ]
        read_only_fields = ['id', 'cost']

    def create(self, validated_data):
        code = validated_data.pop('referral_code', None)
        referral = None
        if code:
            try:
                referral = Referral.objects.get(code=code, is_active=True)
                # increment usage
                referral.times_used = models.F('times_used') + 1
                referral.save()
            except Referral.DoesNotExist:
                raise serializers.ValidationError({"referral_code": "Invalid or inactive code"})

        user = None
        req = self.context.get('request')
        if req and req.user and req.user.is_authenticated:
            user = req.user

        booking = Booking.objects.create(
            user            = user,
            box_type        = validated_data['box_type'],
            quantity        = validated_data['quantity'],
            pickup_address  = validated_data['pickup_address'],
            pickup_date     = validated_data['pickup_date'],
            pickup_slot     = validated_data['pickup_slot'],
            referral        = referral,
            # `cost` and `reference_code` are set in model.save()
        )
        return booking


class BookingDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Booking
        fields = [
            'id','user','box_type','quantity',
            'pickup_address','pickup_date','pickup_slot',
            'referral','cost','reference_code','created_at'
        ]
        read_only_fields = fields


class BookingTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Booking
        fields = [
            'reference_code','box_type','quantity',
            'pickup_address','pickup_date','pickup_slot',
            'cost','created_at'
        ]
        read_only_fields = fields
