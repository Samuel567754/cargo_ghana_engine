import pytest
from django.contrib.auth import get_user_model

User = get_user_model()
pytestmark = pytest.mark.django_db

def test_create_user():
    user = User.objects.create_user(
        username='testuser',
        email='test@user.com',
        password='testpass123'
    )
    assert user.username == 'testuser'
    assert user.email == 'test@user.com'
    assert not user.is_staff
    assert not user.is_superuser
    assert not user.is_agent

def test_create_agent_user():
    user = User.objects.create_user(
        username='agentuser',
        email='agent@user.com',
        password='testpass123',
        is_agent=True
    )
    assert user.is_agent