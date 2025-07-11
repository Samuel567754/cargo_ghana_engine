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

def test_create_tracking_record(api_client, booking):
    url = reverse('tracking-list')
    payload = {
        'booking': booking.id,
        'status': 'In Transit',
        'location': 'Warehouse A'
    }
    response = api_client.post(url, payload)
    assert response.status_code == 201
    data = response.json()
    assert data['status'] == 'In Transit'
    assert data['location'] == 'Warehouse A'

def test_tracking_record_str(tracking_record):
    expected_str = f'{tracking_record.booking.id} - {tracking_record.status}'
    assert str(tracking_record) == expected_str

# Add these new test functions

def test_tracking_record_ordering(api_client, booking):
    # Create records in non-chronological order
    TrackingRecord.objects.create(
        booking=booking,
        status='Delivered',
        location='Final Destination'
    )
    TrackingRecord.objects.create(
        booking=booking,
        status='In Transit',
        location='Warehouse B'
    )
    
    url = reverse('tracking-list')
    resp = api_client.get(url)
    data = resp.json()
    
    # Verify chronological ordering
    assert data[0]['status'] == 'In Transit'
    assert data[1]['status'] == 'Delivered'

def test_tracking_filter_by_booking(api_client, booking):
    TrackingRecord.objects.create(
        booking=booking,
        status='In Transit',
        location='Warehouse A'
    )
    
    url = reverse('tracking-list')
    resp = api_client.get(url, {'booking': booking.id})
    data = resp.json()
    
    assert len(data) == 1
    assert data[0]['booking'] == booking.id
