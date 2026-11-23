"""Настройка административного интерфейса для пользователей."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Админка пользователя с полями роли и учебной группы."""

    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Профиль платформы', {'fields': ('role', 'group_name')}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ('Профиль платформы', {'fields': ('role', 'group_name')}),
    )
    list_display = ('username', 'email', 'role', 'group_name', 'is_staff', 'is_active')
    list_filter = DjangoUserAdmin.list_filter + ('role',)
    search_fields = ('username', 'email', 'group_name')