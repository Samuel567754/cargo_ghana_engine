from rest_framework import serializers
from .models import BoxType, Booking

class ContainerProgressSerializer(serializers.Serializer):
    total_volume = serializers.DecimalField(max_digits=8, decimal_places=2)
    goal_volume = serializers.DecimalField(max_digits=8, decimal_places=2)
    percent = serializers.DecimalField(max_digits=5, decimal_places=2)

class BoxTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoxType
        fields = '__all__'

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        read_only_fields = ('id', 'created_at', 'cost')
        fields = ['id', 'box_type', 'weight_kg', 'pickup_address',
                  'pickup_date', 'pickup_slot', 'cost', 'created_at']

    def create(self, validated_data):
        # calculate cost = price_per_box + (weight_kg * price_per_kg)
        box = validated_data['box_type']
        cost = box.price_per_box + (validated_data['weight_kg'] * box.price_per_kg)
        validated_data['cost'] = cost
        return super().create(validated_data)
