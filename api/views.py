"""Эндпоинты REST API платформы учебных материалов."""
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions

from materials.models import Category, DownloadLog, Material

from .permissions import IsOwnerOrTeacherOrReadOnly
from .serializers import (
    CategorySerializer,
    DownloadLogSerializer,
    MaterialSerializer,
)


def _visible_materials(user):
    """Возвращает queryset материалов, доступных пользователю."""
    queryset = Material.objects.select_related('category', 'author').prefetch_related('tags')
    if not getattr(user, 'is_teacher', False):
        queryset = queryset.filter(
            Q(visibility=Material.Visibility.PUBLIC) | Q(author=user)
        ).filter(Q(is_published=True) | Q(author=user))
    return queryset


class CategoryListView(generics.ListAPIView):
    """GET /api/categories/ — список категорий."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class MaterialListCreateView(generics.ListCreateAPIView):
    """GET /api/materials/ и POST /api/materials/ — список и создание."""

    serializer_class = MaterialSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Фильтрация по категории и поиск по названию/описанию."""
        queryset = _visible_materials(self.request.user)

        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            ).distinct()

        return queryset

    def perform_create(self, serializer):
        """Автором всегда становится текущий пользователь."""
        serializer.save(author=self.request.user)


class MaterialDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE /api/materials/<id>/."""

    serializer_class = MaterialSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrTeacherOrReadOnly]

    def get_queryset(self):
        """Пользователь видит только доступные ему материалы."""
        return _visible_materials(self.request.user)


class MaterialDownloadLogView(generics.ListAPIView):
    """GET /api/materials/<id>/downloads/ — журнал скачиваний материала."""

    serializer_class = DownloadLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Доступ к журналу — только у автора и преподавателей."""
        material = get_object_or_404(Material, pk=self.kwargs['pk'])
        if not material.can_edit(self.request.user):
            raise PermissionDenied('Журнал доступен только автору или преподавателю.')
        return DownloadLog.objects.filter(material=material).select_related('user')