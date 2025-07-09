import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from django.urls import reverse

from bookings.models import BoxType, Booking
from tracking.models import TrackingRecord

pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def box_type():
    return BoxType.objects.create(
        name='Medium',
        length_cm=20, width_cm=20, height_cm=20,
        price_per_kg=Decimal('3.00'),
        price_per_box=Decimal('25.00'),
    )

@pytest.fixture
def booking(box_type):
    # create with quantity instead of weight
    return Booking.objects.create(
        box_type=box_type,
        quantity=2,
        pickup_address='123 A St',
        pickup_date='2025-08-01',
        pickup_slot='Afternoon',
        user=None,
    )

@pytest.fixture
def tracking_record(booking):
    return TrackingRecord.objects.create(
        booking=booking,
        status='In Transit',
        location='Accra Warehouse'
    )

def test_list_tracking_records(api_client, tracking_record):
    url = reverse('tracking-list')
    resp = api_client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    assert any(r['status'] == 'In Transit' for r in data)
