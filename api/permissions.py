"""Пользовательские permissions для DRF."""
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrTeacherOrReadOnly(BasePermission):
    """Изменять материал может только автор или преподаватель."""

    message = 'Изменять материал может только автор или преподаватель.'

    def has_object_permission(self, request, view, obj) -> bool:
        """Разделяет права на чтение и на изменение."""
        if request.method in SAFE_METHODS:
            return obj.can_view(request.user)
        return obj.can_edit(request.user)