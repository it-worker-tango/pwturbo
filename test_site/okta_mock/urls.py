"""模拟 OKTA 的 URL 路由"""
from django.urls import path
from . import views

urlpatterns = [
    path("authorize/", views.authorize, name="okta_authorize"),
    path("callback/", views.callback, name="okta_callback"),
    path("userinfo/", views.token_info, name="okta_userinfo"),
]
