import pytest
from django.utils import timezone
from decimal import Decimal
from ..models import Referral
from bookings.models import Booking, BoxType

pytestmark = pytest.mark.django_db

@pytest.fixture
def box_type():
    return BoxType.objects.create(
        name='Test Box',
        length_cm=10,
        width_cm=10,
        height_cm=10,
        price_per_kg=Decimal('2.50'),
        price_per_box=Decimal('10.00')
    )

@pytest.fixture
def booking(box_type):
    volume = (
        Decimal(box_type.length_cm) / 100 *
        Decimal(box_type.width_cm) / 100 *
        Decimal(box_type.height_cm) / 100
    )
    cost = volume * Decimal('453.66')
    
    return Booking.objects.create(
        box_type=box_type,
        quantity=1,
        pickup_address="Test Address",
        pickup_date="2025-01-01",
        pickup_slot="Morning",
        cost=cost
    )

@pytest.fixture
def referral():
    return Referral.objects.create(
        email='test@example.com',
        code='TEST123',
        reward_amount=Decimal('0.00')
    )

def test_track_click(referral):
    initial_clicks = referral.link_clicks
    referral.track_click()
    assert referral.link_clicks == initial_clicks + 1
    assert referral.last_clicked_at is not None

def test_track_successful_referral(referral, booking):
    initial_reward = referral.reward_amount
    referral.track_successful_referral(booking)
    assert referral.successful_referrals == 1
    assert referral.total_referrals == 1
    assert referral.reward_amount > initial_reward