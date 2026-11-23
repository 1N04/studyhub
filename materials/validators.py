"""Валидаторы загружаемых файлов."""
import os

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_file_extension(value) -> None:
    """Проверяет расширение файла по белому списку из настроек."""
    extension = os.path.splitext(value.name)[1].lower()
    allowed = getattr(
        settings,
        'ALLOWED_UPLOAD_EXTENSIONS',
        ['.pdf', '.docx', '.pptx', '.xlsx', '.zip', '.txt'],
    )
    if extension not in allowed:
        raise ValidationError(
            f'Недопустимый тип файла «{extension}». '
            f'Разрешены: {", ".join(allowed)}.'
        )


def validate_file_size(value) -> None:
    """Проверяет предельный размер файла (по умолчанию 10 МБ)."""
    limit = getattr(settings, 'MAX_UPLOAD_SIZE', 10 * 1024 * 1024)
    if value.size > limit:
        raise ValidationError(
            f'Размер файла не должен превышать {limit // (1024 * 1024)} МБ.'
        )