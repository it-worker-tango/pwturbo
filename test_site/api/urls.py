from django.urls import path
from . import views

urlpatterns = [
    path('user/', views.user_info, name='api_user_info'),
    path('data/', views.test_data, name='api_test_data'),
    path('download/csv/', views.download_csv, name='api_download_csv'),
    path('download/json/', views.download_json, name='api_download_json'),
]
