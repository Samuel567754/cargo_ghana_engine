import os
from django.conf import settings
from django.http import FileResponse, Http404

def serve_cheatsheet(request):
    path = os.path.join(settings.BASE_DIR, 'static', 'docs', 'cheatsheet.pdf')
    if not os.path.exists(path):
        raise Http404("Cheat sheet not found.")
    return FileResponse(open(path, 'rb'), as_attachment=True, filename='cheatsheet.pdf')
