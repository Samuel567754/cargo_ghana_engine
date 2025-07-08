# bookings/serializers.py
from decimal import Decimal
from rest_framework import serializers
from .models import BoxType, Booking

# ──────────────────────────────────────────────────
# 1) Progress serializer (for ContainerProgressView)
class ContainerProgressSerializer(serializers.Serializer):
    total_volume = serializers.DecimalField(max_digits=8, decimal_places=2)
    goal_volume  = serializers.DecimalField(max_digits=8, decimal_places=2)
    percent      = serializers.DecimalField(max_digits=5, decimal_places=2)

# ──────────────────────────────────────────────────
# 2) BoxType (read‑only)
class BoxTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = BoxType
        fields = '__all__'

# ──────────────────────────────────────────────────
# 3) Volume calculator
class VolumeCalcItemSerializer(serializers.Serializer):
    type_id  = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

class VolumeCalcSerializer(serializers.Serializer):
    boxes = serializers.ListSerializer(
        child=VolumeCalcItemSerializer(),
        allow_empty=False
    )
    total_volume = serializers.FloatField(read_only=True)
    total_cost   = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    def validate(self, data):
        type_ids = [item['type_id'] for item in data['boxes']]
        existing = set(BoxType.objects.filter(id__in=type_ids)
                                  .values_list('id', flat=True))
        missing = set(type_ids) - existing
        if missing:
            raise serializers.ValidationError(f"BoxType(s) not found: {missing}")
        return data

    def create(self, validated_data):
        total_vol  = Decimal('0')
        total_cost = Decimal('0')
        for item in validated_data['boxes']:
            bt  = BoxType.objects.get(id=item['type_id'])
            qty = item['quantity']
            total_vol  += bt.volume_m3 * qty
            total_cost += bt.price_per_box * qty

        return {
            'total_volume': float(total_vol.quantize(Decimal('0.01'))),
            'total_cost':   total_cost.quantize(Decimal('0.01'))
        }

# ──────────────────────────────────────────────────
# 4) Booking serializers
class BookingCreateSerializer(serializers.ModelSerializer):
    """
    For POST /bookings/:
    - returns id and cost back to the client
    """
    id   = serializers.IntegerField(read_only=True)
    cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id',
            'box_type',
            'weight_kg',
            'pickup_address',
            'pickup_date',
            'pickup_slot',
            'cost',
        ]
        read_only_fields = ['id', 'cost']

    def create(self, validated_data):
        # compute cost = price_per_box + (weight_kg * price_per_kg)
        box  = validated_data['box_type']
        cost = box.price_per_box + (validated_data['weight_kg'] * box.price_per_kg)
        validated_data['cost'] = cost.quantize(Decimal('0.01'))
        return super().create(validated_data)


class BookingDetailSerializer(serializers.ModelSerializer):
    """
    For GET /bookings/ and GET /bookings/{id}/:
    - returns all relevant booking info including cost & reference_code
    """
    class Meta:
        model = Booking
        fields = [
            'id',
            'user',
            'box_type',
            'weight_kg',
            'pickup_address',
            'pickup_date',
            'pickup_slot',
            'cost',
            'reference_code',
            'created_at',
        ]
        read_only_fields = fields



class BookingTrackingSerializer(serializers.ModelSerializer):
    """
    Exposed to the public for booking lookup by reference_code.
    """
    class Meta:
        model = Booking
        fields = [
            'reference_code',
            'box_type',
            'weight_kg',
            'pickup_address',
            'pickup_date',
            'pickup_slot',
            'cost',        
            'created_at',
        ]
        read_only_fields = fields





# from rest_framework import serializers
# from .models import BoxType, Booking
# from decimal import Decimal

# class ContainerProgressSerializer(serializers.Serializer):
#     total_volume = serializers.DecimalField(max_digits=8, decimal_places=2)
#     goal_volume = serializers.DecimalField(max_digits=8, decimal_places=2)
#     percent = serializers.DecimalField(max_digits=5, decimal_places=2)

# class BoxTypeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = BoxType
#         fields = '__all__'

# class BookingSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Booking
#         read_only_fields = ('id', 'created_at', 'cost')
#         fields = ['id', 'box_type', 'weight_kg', 'pickup_address',
#                   'pickup_date', 'pickup_slot', 'cost', 'created_at']

#     def create(self, validated_data):
#         # calculate cost = price_per_box + (weight_kg * price_per_kg)
#         box = validated_data['box_type']
#         cost = box.price_per_box + (validated_data['weight_kg'] * box.price_per_kg)
#         validated_data['cost'] = cost
#         return super().create(validated_data)


# class VolumeCalcItemSerializer(serializers.Serializer):
#     type_id = serializers.IntegerField()
#     quantity = serializers.IntegerField(min_value=1)

# class VolumeCalcSerializer(serializers.Serializer):
#     boxes = serializers.ListSerializer(
#         child=VolumeCalcItemSerializer(),
#         allow_empty=False
#     )
#     total_volume = serializers.FloatField(read_only=True)
#     total_cost = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

#     def validate(self, data):
#         # Ensure all box types exist
#         type_ids = [item['type_id'] for item in data['boxes']]
#         existing = set(BoxType.objects.filter(id__in=type_ids).values_list('id', flat=True))
#         missing = set(type_ids) - existing
#         if missing:
#             raise serializers.ValidationError(f"BoxType(s) not found: {missing}")
#         return data

#     def create(self, validated_data):
#         total_vol = Decimal('0')
#         total_cost = Decimal('0')
#         for item in validated_data['boxes']:
#             bt = BoxType.objects.get(id=item['type_id'])
#             qty = item['quantity']
#             total_vol += bt.volume_m3 * qty
#             total_cost += bt.price_per_box * qty
#         return {
#             'total_volume': float(total_vol),
#             'total_cost': total_cost.quantize(Decimal('0.01'))
#         }
