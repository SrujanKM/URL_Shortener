# shortener/urls.py

from django.urls import path, include
from . import views, api_views

urlpatterns = [
    path('', views.shorten_url, name='shorten_url'),
    path('bulk-upload/', views.bulk_upload, name='bulk_upload'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('download-qr/<str:short_code>/', views.download_qr_code, name='download_qr_code'),
    path('accounts/', include('django.contrib.auth.urls')),  # Include default auth URLs
    path('signup/', views.signup, name='signup'),  # Define signup URL
    path('<str:short_code>/', views.redirect_url, name='redirect_url'),
    path('api/shorten/', api_views.ShortURLCreateAPIView.as_view(), name='api_shorten_url'),
    path('api/shorten/<str:short_code>/', api_views.ShortURLRetrieveAPIView.as_view(), name='api_retrieve_url'),
]
