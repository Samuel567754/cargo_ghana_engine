# bookings/tests/test_public_tracking.py

import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from bookings.models import Booking, BoxType

User = get_user_model()

@pytest.mark.django_db
def test_public_booking_tracking_success():
    # 1) Create a BoxType
    box_type = BoxType.objects.create(
        name="Test Box",
        length_cm=10,
        width_cm=10,
        height_cm=10,
        price_per_kg=Decimal('2.50'),
        price_per_box=Decimal('15.00'),
    )

    # 2) Create a user and a booking
    user = User.objects.create_user(
        username='tracker', email='tracker@example.com', password='password'
    )
    booking = Booking.objects.create(
        user=user,
        box_type=box_type,
        weight_kg=Decimal('5.00'),
        pickup_address='123 Main St',
        pickup_date='2025-08-01',
        pickup_slot='Morning',
        cost=Decimal('27.50'),
    )

    # 3) Hit the public tracking endpoint
    client = APIClient()
    url = reverse('booking-track', kwargs={'reference_code': booking.reference_code})
    resp = client.get(url)

    # 4) Validate response
    assert resp.status_code == 200
    data = resp.json()
    assert data['reference_code'] == booking.reference_code
    assert data['box_type'] == box_type.id
    assert data['weight_kg'] == '5.00'
    assert data['pickup_address'] == '123 Main St'
    assert data['pickup_slot'] == 'Morning'
    assert data['cost'] == '27.50'
    assert 'created_at' in data

@pytest.mark.django_db
def test_public_booking_tracking_not_found():
    client = APIClient()
    url = reverse('booking-track', kwargs={'reference_code': 'NONEXISTENT'})
    resp = client.get(url)
    assert resp.status_code == 404
