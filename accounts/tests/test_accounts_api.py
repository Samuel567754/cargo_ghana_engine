import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()
pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    return APIClient()

def test_user_registration(api_client):
    url = reverse('users-register')
    payload = {
        'username': 'newuser',
        'email': 'new@user.com',
        'password': 'secret123'
    }
    resp = api_client.post(url, payload, format='json')
    assert resp.status_code == 201
    data = resp.json()
    assert data['username'] == 'newuser'
    assert 'id' in data

def test_me_unauthenticated(api_client):
    url = reverse('users-me')
    resp = api_client.get(url)
    assert resp.status_code == 403  # Forbidden for unauthenticated

def test_me_authenticated(api_client):
    user = User.objects.create_user(username='u', password='p')
    api_client.force_authenticate(user=user)
    url = reverse('users-me')
    resp = api_client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    assert data['username'] == 'u'
