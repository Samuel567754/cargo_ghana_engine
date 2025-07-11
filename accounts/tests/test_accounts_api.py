import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()
pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user_data():
    return {
        'username': 'newuser',
        'email': 'new@user.com',
        'password': 'secret123'
    }

def test_user_registration(api_client, user_data):
    url = reverse('users-register')
    resp = api_client.post(url, user_data, format='json')
    assert resp.status_code == 201
    data = resp.json()
    assert data['username'] == user_data['username']
    assert 'id' in data
    assert User.objects.filter(username=user_data['username']).exists()

def test_user_registration_duplicate_username(api_client, user_data):
    # Create first user
    User.objects.create_user(**user_data)
    # Try to create duplicate
    url = reverse('users-register')
    resp = api_client.post(url, user_data, format='json')
    assert resp.status_code == 400
    assert 'username' in resp.json()

def test_me_unauthenticated(api_client):
    url = reverse('users-me')
    resp = api_client.get(url)
    assert resp.status_code == 403

def test_me_authenticated(api_client, user_data):
    user = User.objects.create_user(**user_data)
    api_client.force_authenticate(user=user)
    url = reverse('users-me')
    resp = api_client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    assert data['username'] == user_data['username']
    assert data['email'] == user_data['email']

def test_user_login(api_client, user_data):
    User.objects.create_user(**user_data)
    url = reverse('users-login')
    resp = api_client.post(url, {
        'username': user_data['username'],
        'password': user_data['password']
    }, format='json')
    assert resp.status_code == 200
    assert 'access' in resp.json()  # Changed from 'token' to 'access'
