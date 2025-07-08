import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from agents.models import AgentApplication
from django.contrib.auth import get_user_model

User = get_user_model()
pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user():
    return User.objects.create_superuser(username='admin', password='pass')

def test_create_agent_application(api_client):
    url = reverse('agents-list')
    payload = {
        'name': 'Jane Doe',
        'email': 'jane@doe.com',
        'phone': '0551234567',
        'company': 'FastTrans',
        'experience': '5 years in logistics'
    }
    resp = api_client.post(url, payload, format='json')
    assert resp.status_code == 201
    body = resp.json()
    assert body['name'] == 'Jane Doe'
    assert body['approved'] is False

def test_list_agents_anonymous_forbidden(api_client):
    url = reverse('agents-list')
    resp = api_client.get(url)
    assert resp.status_code == 403

def test_list_agents_admin(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    AgentApplication.objects.create(
        name='Joe Bloggs', email='joe@bloggs.com',
        phone='0557654321', company='', experience=''
    )
    url = reverse('agents-list')
    resp = api_client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]['name'] == 'Joe Bloggs'
