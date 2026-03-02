"""URL configuration for test_site project."""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('api/', include('api.urls')),
    path('okta/', include('okta_mock.urls')),
    path('', include('accounts.urls')),
]
