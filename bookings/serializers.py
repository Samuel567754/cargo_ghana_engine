from django.db import models
from rest_framework import serializers
from decimal import Decimal
from .models import BoxType, Booking, ContainerBatch, ContainerCapacity  # Add ContainerCapacity here
from referrals.models import Referral
from .models import CONTAINER_MAX_VOLUME, MAX_BOXES_PER_TYPE
from datetime import datetime, date
from django.utils import timezone
from .models import PICKUP_SLOTS, MIN_PICKUP_DAYS, MAX_PICKUP_DAYS


class ContainerProgressSerializer(serializers.Serializer):
    total_volume = serializers.DecimalField(max_digits=10, decimal_places=2)
    goal_volume  = serializers.DecimalField(max_digits=10, decimal_places=2)
    percent      = serializers.DecimalField(max_digits=5, decimal_places=2)


class BoxTypeSerializer(serializers.ModelSerializer):
    volume_m3 = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = BoxType
        fields = ['id', 'name', 'length_cm', 'width_cm', 'height_cm', 
                 'price_per_kg', 'price_per_box', 'volume_m3']


class VolumeCalcItemSerializer(serializers.Serializer):
    type_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, max_value=MAX_BOXES_PER_TYPE)
    volume = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

class VolumeCalcSerializer(serializers.Serializer):
    boxes = serializers.ListSerializer(child=VolumeCalcItemSerializer(), allow_empty=False)
    total_volume = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_applied = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    original_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    def validate(self, data):
        validated_data = super().validate(data)
        total_volume = 0
        total_cost = 0
        items_details = []

        for item in validated_data['items']:
            box_type = BoxType.objects.get(id=item['box_type_id'])
            quantity = item['quantity']
            
            # Calculate volume and cost for this item
            item_volume = box_type.volume_m3 * quantity
            item_cost = box_type.price_per_box * quantity
            
            items_details.append({
                'box_type': box_type.name,
                'quantity': quantity,
                'volume_m3': round(item_volume, 3),
                'cost': round(item_cost, 2)
            })
            
            total_volume += item_volume
            total_cost += item_cost

        # Apply volume-based discounts
        discount = 0
        if total_volume >= 10:
            discount = 0.15  # 15% discount for volume >= 10m³
        elif total_volume >= 5:
            discount = 0.10  # 10% discount for volume >= 5m³
        elif total_volume >= 2:
            discount = 0.05  # 5% discount for volume >= 2m³

        final_cost = total_cost * (1 - discount)

        validated_data['calculation_details'] = {
            'items': items_details,
            'total_volume_m3': round(total_volume, 3),
            'original_cost': round(total_cost, 2),
            'discount_percentage': discount * 100 if discount > 0 else 0,
            'final_cost': round(final_cost, 2)
        }

        return validated_data

    def create(self, validated_data):
        result = {
            'boxes': [],
            'total_volume': Decimal('0'),
            'total_cost': Decimal('0'),
            'discount_applied': Decimal('0'),
            'original_cost': Decimal('0')
        }
        
        # Calculate volumes and costs
        for item in validated_data['boxes']:
            box_type = BoxType.objects.get(id=item['type_id'])
            quantity = item['quantity']
            volume = box_type.volume_m3 * quantity
            cost = volume * Decimal('453.66')
            
            result['boxes'].append({
                'type_id': item['type_id'],
                'quantity': quantity,
                'volume': volume.quantize(Decimal('0.01')),
                'cost': cost.quantize(Decimal('0.01'))
            })
            
            result['total_volume'] += volume
            result['original_cost'] += cost
        
        # Apply volume-based discount
        total_volume = result['total_volume']
        discount = Decimal('0')
        for threshold, discount_rate in sorted(VOLUME_DISCOUNTS.items(), reverse=True):
            if total_volume >= threshold:
                discount = discount_rate
                break

        result['total_volume'] = result['total_volume'].quantize(Decimal('0.01'))
        result['original_cost'] = result['original_cost'].quantize(Decimal('0.01'))
        result['discount_applied'] = discount
        result['total_cost'] = (result['original_cost'] * (1 - discount)).quantize(Decimal('0.01'))
        
        return result


class BookingCreateSerializer(serializers.ModelSerializer):
    id            = serializers.UUIDField(read_only=True)
    quantity      = serializers.IntegerField(min_value=1)
    referral_code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    cost          = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    pickup_slot = serializers.ChoiceField(choices=PICKUP_SLOTS)

    def validate_pickup_date(self, value):
        today = timezone.now().date()
        min_date = today + timedelta(days=MIN_PICKUP_DAYS)
        max_date = today + timedelta(days=MAX_PICKUP_DAYS)

        if value < min_date:
            raise serializers.ValidationError(
                f"Pickup must be at least {MIN_PICKUP_DAYS} day(s) in advance."
            )
        if value > max_date:
            raise serializers.ValidationError(
                f"Pickup cannot be more than {MAX_PICKUP_DAYS} days in advance."
            )
        
        # Validate weekday (no pickups on Sundays)
        if value.weekday() == 6:  # Sunday
            raise serializers.ValidationError("Pickups are not available on Sundays.")

        return value

    def validate(self, data):
        data = super().validate(data)
        
        # Additional validation can be added here if needed
        # For example, checking if the selected slot is still available
        
        return data

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


class ContainerCapacitySerializer(serializers.ModelSerializer):
    percentage_filled = serializers.SerializerMethodField()
    status_color = serializers.SerializerMethodField()

    class Meta:
        model = ContainerCapacity
        fields = ['total_volume', 'remaining_volume', 'booking_count', 
                 'percentage_filled', 'status_color', 'timestamp']

    def get_percentage_filled(self, obj) -> Decimal:
        batch_capacity = obj.batch.target_volume
        if batch_capacity > 0:
            return (obj.total_volume / batch_capacity * 100).quantize(Decimal('0.01'))
        return Decimal('0')

    def get_status_color(self, obj) -> str:
        percentage = self.get_percentage_filled(obj)
        if percentage >= 90:
            return 'red'  # Almost full
        elif percentage >= 75:
            return 'orange'  # Getting full
        elif percentage >= 50:
            return 'yellow'  # Half full
        return 'green'  # Plenty of space
