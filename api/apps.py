"""Конфигурация приложения api."""
from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Регистрирует REST API платформы."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    verbose_name = 'REST API'