import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from referrals.models import Referral
from django.contrib.auth import get_user_model

User = get_user_model()
pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user():
    return User.objects.create_superuser(username='admin', password='pass')

def test_create_referral_anonymous(api_client):
    url = reverse('referrals-list')
    resp = api_client.post(url, {'email': 'x@y.com'}, format='json')
    assert resp.status_code == 201
    body = resp.json()
    assert body['email'] == 'x@y.com'
    assert 'code' in body

def test_list_referrals_anonymous_forbidden(api_client):
    url = reverse('referrals-list')
    resp = api_client.get(url)
    assert resp.status_code == 403

def test_list_referrals_admin(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    Referral.objects.create(email='a@b.com', code='ABC123XYZ789', reward_amount=10)
    url = reverse('referrals-list')
    resp = api_client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]['email'] == 'a@b.com'
