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
    path('printer-settings/', views.printer_settings, name='printer_settings'),
    
    # Admin UPC Management
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),
    path('admin-upc/', views.admin_upc, name='admin_upc'),
    path('api/admin-upload-csv/', views.admin_upload_csv, name='admin_upload_csv'),
    path('api/admin-update-upc/', views.admin_update_upc, name='admin_update_upc'),
    path('admin-download-template/', views.admin_download_template, name='admin_download_template'),
]
