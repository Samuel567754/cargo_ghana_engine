import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from bookings.models import BoxType, Booking

User = get_user_model()
pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user():
    return User.objects.create_user(username='testuser', password='password123')

@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client

@pytest.fixture
def box_type():
    return BoxType.objects.create(
        name='Small',
        length_cm=10, width_cm=10, height_cm=10,
        price_per_kg=Decimal('2.50'),
        price_per_box=Decimal('15.00'),
    )

def test_list_box_types(api_client, box_type):
    url = reverse('boxes-list')
    resp = api_client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    assert any(item['name'] == 'Small' for item in data)

def test_create_booking(auth_client, box_type):
    url = reverse('bookings-list')
    payload = {
        'box_type': box_type.id,
        'quantity': 5,
        'pickup_address': '123 Main St',
        'pickup_date': '2025-08-01',
        'pickup_slot': 'Morning'
    }
    resp = auth_client.post(url, payload, format='json')
    assert resp.status_code == 201, resp.content
    body = resp.json()

    volume = (Decimal(box_type.length_cm)/100
              * Decimal(box_type.width_cm)/100
              * Decimal(box_type.height_cm)/100)
    expected_cost = (volume * 5 * Decimal('453.66')).quantize(Decimal('0.01'))

    assert Decimal(body['cost']) == expected_cost
    assert 'id' in body

    booking = Booking.objects.get(id=body['id'])
    assert booking.cost == expected_cost
