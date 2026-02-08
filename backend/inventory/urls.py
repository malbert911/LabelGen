from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.home, name='home'),
    path('generate/', views.bulk_generate, name='bulk_generate'),
    path('api/process-bulk-scans/', views.process_bulk_scans, name='process_bulk_scans'),
    path('box-label/', views.box_label, name='box_label'),
    path('api/lookup-serial/', views.lookup_serial, name='lookup_serial'),
    path('reprint/', views.reprint, name='reprint'),
]
