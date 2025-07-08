from django.urls import path
from core.views import serve_cheatsheet

urlpatterns = [
    # … other patterns …
    path('download/cheatsheet/', serve_cheatsheet, name='download-cheatsheet'),
]
