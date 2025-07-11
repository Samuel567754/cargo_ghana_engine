import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from agents.models import AgentApplication
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()
pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user():
    return User.objects.create_superuser(username='admin', password='pass')

def test_create_agent_application(api_client):
    url = reverse('agent-applications-list')
    # Create test files
    pdf_content = b'%PDF-1.4 test content'
    id_doc = SimpleUploadedFile("id.pdf", pdf_content, content_type="application/pdf")
    resume = SimpleUploadedFile("resume.pdf", pdf_content, content_type="application/pdf")
    
    payload = {
        'name': 'Jane Doe',
        'email': 'jane@doe.com',
        'phone': '0551234567',
        'company': 'FastTrans',
        'experience': '5 years in logistics',
        'id_document': id_doc,
        'resume': resume
    }
    resp = api_client.post(url, payload, format='multipart')  # Changed format to multipart
    assert resp.status_code == 201
    body = resp.json()
    assert body['name'] == 'Jane Doe'
    assert body['status'] == 'pending'  # Changed from 'approved' to match default status

def test_list_agents_anonymous_forbidden(api_client):
    url = reverse('agent-applications-list')  # Changed from 'agents-list'
    resp = api_client.get(url)
    assert resp.status_code == 403

def test_list_agents_admin(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    AgentApplication.objects.create(
        name='Joe Bloggs', email='joe@bloggs.com',
        phone='0557654321', company='', experience=''
    )
    url = reverse('agent-applications-list')  # Changed from 'agents-list'
    resp = api_client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]['name'] == 'Joe Bloggs'


def test_agent_application_validation():
    # Test document validation for new applications
    application = AgentApplication(
        name="Test Agent",
        email="test@agent.com",
        phone="1234567890"
    )
    with pytest.raises(ValidationError) as exc_info:
        # Call full_clean() to trigger validation
        application.full_clean()
    
    assert 'id_document' in str(exc_info.value)
    assert 'resume' in str(exc_info.value)

def test_agent_application_with_documents(api_client):
    # Create test files
    pdf_content = b'%PDF-1.4 test content'
    id_doc = SimpleUploadedFile("id.pdf", pdf_content, content_type="application/pdf")
    resume = SimpleUploadedFile("resume.pdf", pdf_content, content_type="application/pdf")
    
    url = reverse('agent-applications-list')  # Changed from 'agents-list'
    payload = {
        'name': 'Test Agent',
        'email': 'test@agent.com',
        'phone': '1234567890',
        'company': 'Test Company',
        'experience': 'Test Experience',
        'id_document': id_doc,
        'resume': resume
    }
    
    response = api_client.post(url, payload, format='multipart')
    assert response.status_code == 201
