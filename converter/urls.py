from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/upload/', views.upload_and_convert, name='upload_and_convert'),
    path('api/download/', views.download_json, name='download_json'),
    path('api/transform-tables/', views.transform_to_tables, name='transform_to_tables'),
    path('api/resolve-headers/', views.resolve_headers, name='resolve_headers'),
    path('api/health/', views.health_check, name='health_check'),
    path('favicon.ico', RedirectView.as_view(url='/static/images/favicon.ico'), name='favicon'),
] 