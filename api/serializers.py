"""Сериализаторы DRF для материалов, категорий и журнала скачиваний."""
from rest_framework import serializers

from materials.models import Category, DownloadLog, Material, Tag
from materials.validators import validate_file_extension, validate_file_size


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор категории с числом материалов."""

    materials_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'materials_count')
        read_only_fields = ('slug',)

    def get_materials_count(self, obj: Category) -> int:
        """Возвращает количество материалов в категории."""
        return obj.materials.count()


class MaterialSerializer(serializers.ModelSerializer):
    """Сериализатор учебного материала."""

    author = serializers.CharField(source='author.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    tags = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Tag.objects.all(),
        required=False,
    )

    class Meta:
        model = Material
        fields = (
            'id', 'title', 'description', 'file', 'category', 'category_name',
            'author', 'tags', 'visibility', 'downloads_count',
            'uploaded_at', 'updated_at',
        )
        read_only_fields = ('downloads_count', 'uploaded_at', 'updated_at', 'author')

    def validate_title(self, value: str) -> str:
        """Проверяет минимальную длину названия."""
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError(
                'Название должно содержать не менее 3 символов.'
            )
        return value

    def validate_file(self, value):
        """Применяет к файлу те же валидаторы, что и в ModelForm."""
        validate_file_extension(value)
        validate_file_size(value)
        return value


class DownloadLogSerializer(serializers.ModelSerializer):
    """Сериализатор записи журнала скачиваний."""

    user = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = DownloadLog
        fields = ('id', 'user', 'ip_address', 'downloaded_at')