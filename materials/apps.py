"""Конфигурация приложения materials."""
from django.apps import AppConfig


class MaterialsConfig(AppConfig):
    """Регистрирует приложение учебных материалов."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'materials'
    verbose_name = 'Учебные материалы'