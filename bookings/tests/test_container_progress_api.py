import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from django.urls import reverse
from bookings.models import BoxType, Booking

pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def box_small():
    # 1m × 1m × 1m = 1.00 m³
    return BoxType.objects.create(
        name='Cube1',
        length_cm=100, width_cm=100, height_cm=100,
        price_per_kg=1.00, price_per_box=5.00
    )

@pytest.fixture
def box_large():
    # 2m × 2m × 2m = 8.00 m³
    return BoxType.objects.create(
        name='Cube2',
        length_cm=200, width_cm=200, height_cm=200,
        price_per_kg=1.00, price_per_box=10.00
    )

@pytest.fixture(autouse=True)
def make_bookings(box_small, box_large):
    # Create two bookings: 1 × 1m³ and 1 × 8m³ → total 9.00 m³
    Booking.objects.create(box_type=box_small, weight_kg=1, pickup_address='A', pickup_date='2025-08-01', pickup_slot='Morning', user=None)
    Booking.objects.create(box_type=box_large, weight_kg=1, pickup_address='B', pickup_date='2025-08-02', pickup_slot='Afternoon', user=None)

def test_container_progress(api_client):
    url = reverse('container-progress')
    resp = api_client.get(url)
    assert resp.status_code == 200, resp.content

    data = resp.json()
    # total_volume should be 9.00
    assert Decimal(data['total_volume']) == Decimal('9.00')
    # goal 66.16
    assert Decimal(data['goal_volume']) == Decimal('66.16')
    # percent = 9 / 66.16 * 100 ≈ 13.60%
    expected_pct = (Decimal('9.00') / Decimal('66.16') * 100).quantize(Decimal('0.01'))
    assert Decimal(data['percent']) == expected_pct
