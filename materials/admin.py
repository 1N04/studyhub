"""Административный интерфейс для учебных материалов."""
from django.contrib import admin

from .models import Category, DownloadLog, Material, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Управление категориями."""

    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Управление тегами."""

    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    """Управление учебными материалами и модерация."""

    list_display = (
        'title', 'category', 'author', 'visibility',
        'is_published', 'downloads_count', 'uploaded_at',
    )
    list_filter = ('category', 'visibility', 'is_published', 'uploaded_at')
    search_fields = ('title', 'description', 'author__username')
    autocomplete_fields = ('category', 'author')
    filter_horizontal = ('tags',)
    readonly_fields = ('downloads_count', 'uploaded_at', 'updated_at')
    date_hierarchy = 'uploaded_at'
    actions = ('publish', 'unpublish')

    @admin.action(description='Опубликовать выбранные материалы')
    def publish(self, request, queryset):
        """Возвращает материалы в публичный список."""
        queryset.update(is_published=True)

    @admin.action(description='Снять с публикации')
    def unpublish(self, request, queryset):
        """Скрывает материалы из общего списка."""
        queryset.update(is_published=False)


@admin.register(DownloadLog)
class DownloadLogAdmin(admin.ModelAdmin):
    """Просмотр журнала скачиваний (только чтение)."""

    list_display = ('material', 'user', 'ip_address', 'downloaded_at')
    list_filter = ('downloaded_at',)
    search_fields = ('material__title', 'user__username')
    readonly_fields = ('material', 'user', 'ip_address', 'downloaded_at')

    def has_add_permission(self, request):
        """Записи журнала создаются автоматически."""
        return False