"""Модели предметной области: категории, теги, материалы, журнал скачиваний."""
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from .validators import validate_file_extension, validate_file_size


class Category(models.Model):
    """Категория (учебный предмет) материала."""

    name = models.CharField('Название', max_length=120, unique=True)
    slug = models.SlugField('Слаг', max_length=140, unique=True, blank=True)
    description = models.TextField('Описание', blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        """Автоматически формирует слаг из названия."""
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)[:140]
        super().save(*args, **kwargs)


class Tag(models.Model):
    """Тег для дополнительной классификации материала (M2M)."""

    name = models.CharField('Название', max_length=50, unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Material(models.Model):
    """Учебный материал: файл + метаданные + права видимости."""

    class Visibility(models.TextChoices):
        """Уровни видимости материала."""

        PUBLIC = 'public', 'Доступен всем пользователям'
        TEACHERS = 'teachers', 'Только преподавателям'
        PRIVATE = 'private', 'Только автору'

    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True, max_length=2000)
    file = models.FileField(
        'Файл',
        upload_to='materials/%Y/%m/',
        validators=[validate_file_extension, validate_file_size],
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='materials',
        verbose_name='Категория',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='materials',
        verbose_name='Автор',
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='materials',
        verbose_name='Теги',
    )
    visibility = models.CharField(
        'Видимость',
        max_length=16,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
    )
    is_published = models.BooleanField(
        'Опубликован',
        default=True,
        help_text='Снимается преподавателем при модерации.',
    )
    downloads_count = models.PositiveIntegerField(
        'Скачиваний',
        default=0,
        validators=[MinValueValidator(0)],
    )
    uploaded_at = models.DateTimeField('Дата загрузки', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Учебный материал'
        verbose_name_plural = 'Учебные материалы'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['-uploaded_at']),
            models.Index(fields=['visibility']),
        ]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        """Ссылка на детальную страницу материала."""
        return reverse('materials:detail', args=[self.pk])

    def can_view(self, user) -> bool:
        """Проверяет право пользователя на просмотр и скачивание."""
        if self.visibility == self.Visibility.PUBLIC:
            return True
        if not user.is_authenticated:
            return False
        if getattr(user, 'is_teacher', False):
            return True
        return self.author_id == user.id

    def can_edit(self, user) -> bool:
        """Проверяет право на редактирование и удаление."""
        if not user.is_authenticated:
            return False
        return getattr(user, 'is_teacher', False) or self.author_id == user.id


class DownloadLog(models.Model):
    """Журнал скачиваний материала (4-я связанная модель)."""

    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        related_name='downloads',
        verbose_name='Материал',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='downloads',
        verbose_name='Пользователь',
    )
    ip_address = models.GenericIPAddressField('IP-адрес', null=True, blank=True)
    downloaded_at = models.DateTimeField('Дата скачивания', auto_now_add=True)

    class Meta:
        verbose_name = 'Скачивание'
        verbose_name_plural = 'Журнал скачиваний'
        ordering = ['-downloaded_at']

    def __str__(self) -> str:
        return f'{self.material} — {self.user or "аноним"}'