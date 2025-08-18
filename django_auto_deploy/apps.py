from django.apps import AppConfig


class DjangoAutoDeployConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_auto_deploy"
