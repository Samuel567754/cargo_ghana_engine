from django.urls import path
from . import views

urlpatterns = [
    path('container/capacity/', views.ContainerCapacityView.as_view(), name='container-capacity'),
    path('container/capacity/history/', views.CapacityHistoryView.as_view(), name='capacity-history'),
    path('cheatsheet/download/', views.download_box_cheatsheet, name='download_box_cheatsheet'),
]
