"""Модель пользователя с ролевой моделью доступа."""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Пользователь платформы: студент или преподаватель."""

    class Role(models.TextChoices):
        """Допустимые роли пользователя."""

        STUDENT = 'student', 'Студент'
        TEACHER = 'teacher', 'Преподаватель'

    role = models.CharField(
        'Роль',
        max_length=16,
        choices=Role.choices,
        default=Role.STUDENT,
        help_text='Определяет уровень прав в системе.',
    )
    group_name = models.CharField(
        'Учебная группа',
        max_length=32,
        blank=True,
        help_text='Например: ПОВТ-1-24.',
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self) -> str:
        return f'{self.username} ({self.get_role_display()})'

    @property
    def is_teacher(self) -> bool:
        """True, если пользователь имеет права преподавателя."""
        return self.role == self.Role.TEACHER or self.is_superuser