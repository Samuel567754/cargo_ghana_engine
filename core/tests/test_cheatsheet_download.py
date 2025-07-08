import pytest
from django.urls import reverse

@pytest.mark.django_db                   # not strictly needed
def test_cheatsheet_redirect_or_download(client):
    url = reverse('download-cheatsheet')
    resp = client.get(url)
    # If using RedirectView:
    if resp.status_code in (301, 302):
        assert '/static/docs/cheatsheet.pdf' in resp['Location']
    else:
        # If serving directly:
        assert resp.status_code == 200
        assert resp['Content-Type'] == 'application/pdf'
