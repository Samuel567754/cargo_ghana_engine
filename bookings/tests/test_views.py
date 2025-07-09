import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch

from bookings.models import BoxType, Booking

User = get_user_model()
pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user():
    return User.objects.create_superuser(username="admin", email="a@b.com", password="pass")

@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client

@pytest.fixture
def box_small():
    # 1 m³
    return BoxType.objects.create(
        name="Small", length_cm=100, width_cm=100, height_cm=100,
        price_per_kg=Decimal("1.00"), price_per_box=Decimal("5.00")
    )

@pytest.fixture
def box_large():
    # 8 m³
    return BoxType.objects.create(
        name="Large", length_cm=200, width_cm=200, height_cm=200,
        price_per_kg=Decimal("1.00"), price_per_box=Decimal("10.00")
    )

def compute_volume(box: BoxType) -> Decimal:
    return (
        Decimal(box.length_cm)/100 *
        Decimal(box.width_cm)/100  *
        Decimal(box.height_cm)/100
    )

@patch("bookings.models.send_booking_notifications.delay")
def test_create_booking_and_task_enqueue(mock_delay, api_client, box_small):
    """
    - Unauthenticated user can POST /bookings/
    - Cost = volume × quantity × 453.66
    - Task is enqueued exactly once (from model.save)
    """
    url = reverse("bookings-list")
    payload = {
        "box_type": box_small.id,
        "quantity": 4,
        "pickup_address": "123 Elm St",
        "pickup_date": "2025-09-01",
        "pickup_slot": "Morning",
    }
    resp = api_client.post(url, payload, format="json")
    assert resp.status_code == 201, resp.content
    data = resp.json()

    vol = compute_volume(box_small)
    expected_cost = (vol * 4 * Decimal("453.66")).quantize(Decimal("0.01"))
    assert Decimal(data["cost"]) == expected_cost

    # Model.save should enqueue exactly once
    mock_delay.assert_called_once_with(data["id"])

    b = Booking.objects.get(id=data["id"])
    assert b.user is None
    assert b.quantity == 4
    assert b.cost == expected_cost

def test_admin_only_list_and_retrieve(admin_client, box_small):
    """
    Admin can GET list and detail; other users are forbidden.
    """
    b = Booking.objects.create(
        box_type=box_small,
        quantity=1,
        pickup_address="X",
        pickup_date="2025-09-02",
        pickup_slot="Afternoon",
        user=None
    )
    list_url   = reverse("bookings-list")
    detail_url = reverse("bookings-detail", args=[b.id])

    assert admin_client.get(list_url).status_code == 200
    assert admin_client.get(detail_url).status_code == 200

def test_volume_calc(api_client, box_small, box_large):
    url = reverse("volume-calc")
    payload = {
        "boxes": [
            {"type_id": box_small.id, "quantity": 2},
            {"type_id": box_large.id, "quantity": 1},
        ]
    }
    resp = api_client.post(url, payload, format="json")
    assert resp.status_code == 200
    data = resp.json()

    total_vol = compute_volume(box_small)*2 + compute_volume(box_large)*1
    expected_cost = (total_vol * Decimal("453.66")).quantize(Decimal("0.01"))

    assert Decimal(str(data["total_volume"])) == total_vol.quantize(Decimal("0.01"))
    # total_cost now returned as string
    assert Decimal(data["total_cost"]) == expected_cost

def test_container_progress(api_client, box_small, box_large):
    # seed 1×1m³ + 1×8m³ = 9m³
    Booking.objects.create(box_type=box_small, quantity=1,
                           pickup_address="A", pickup_date="2025-09-03", pickup_slot="A", user=None)
    Booking.objects.create(box_type=box_large, quantity=1,
                           pickup_address="B", pickup_date="2025-09-04", pickup_slot="B", user=None)

    url  = reverse("container-progress")
    resp = api_client.get(url)
    assert resp.status_code == 200
    data = resp.json()

    assert Decimal(data["total_volume"]) == Decimal("9.00")
    assert Decimal(data["goal_volume"])  == Decimal("66.16")
    pct = (Decimal("9.00") / Decimal("66.16") * 100).quantize(Decimal("0.01"))
    assert Decimal(data["percent"]) == pct

def test_public_tracking(api_client, box_small):
    b = Booking.objects.create(
        box_type=box_small, quantity=3,
        pickup_address="C", pickup_date="2025-09-05", pickup_slot="C", user=None
    )
    url  = reverse("booking-track", args=[b.reference_code])
    resp = api_client.get(url)
    assert resp.status_code == 200
    data = resp.json()

    expected = (compute_volume(box_small)*3*Decimal("453.66")).quantize(Decimal("0.01"))
    assert Decimal(data["cost"]) == expected
