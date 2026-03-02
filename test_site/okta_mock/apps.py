from django.apps import AppConfig


class OktaMockConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "okta_mock"
    verbose_name = "模拟 OKTA"
