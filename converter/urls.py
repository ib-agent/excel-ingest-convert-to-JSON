from django.urls import path
from django.views.generic import RedirectView
from . import views
from . import pdf_views

urlpatterns = [
    path('', views.main_landing, name='main_landing'),
    path('excel/', views.excel_processor, name='excel_processor'),
    path('pdf/', views.pdf_processor, name='pdf_processor'),
    path('api/upload/', views.upload_and_convert, name='upload_and_convert'),
    path('api/download/', views.download_json, name='download_json'),
    path('api/transform-tables/', views.transform_to_tables, name='transform_to_tables'),
    path('api/resolve-headers/', views.resolve_headers, name='resolve_headers'),
    path('api/health/', views.health_check, name='health_check'),
    path('api/pdf/upload/', pdf_views.upload_and_process_pdf, name='upload_and_process_pdf'),
    path('api/pdf/process/', pdf_views.process_pdf_with_options, name='process_pdf_with_options'),
    path('api/pdf/status/', pdf_views.get_processing_status, name='get_pdf_processing_status'),
    # New table removal endpoint
    path('api/pdf/table-removal/', pdf_views.upload_and_process_pdf_with_table_removal, name='upload_and_process_pdf_table_removal'),
    path('favicon.ico', RedirectView.as_view(url='/static/images/favicon.ico'), name='favicon'),
] 