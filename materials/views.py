"""Представления CRUD для материалов и категорий, скачивание файлов."""
import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import F, ProtectedError, Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import generic

from .forms import CategoryForm, MaterialForm
from .models import Category, DownloadLog, Material


class TeacherRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Пропускает только пользователей с правами преподавателя."""

    raise_exception = True

    def test_func(self) -> bool:
        """Проверка роли текущего пользователя."""
        return getattr(self.request.user, 'is_teacher', False)


class AuthorOrTeacherMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Пропускает автора материала или преподавателя."""

    raise_exception = True

    def test_func(self) -> bool:
        """Проверка прав на конкретный объект."""
        return self.get_object().can_edit(self.request.user)


class MaterialListView(LoginRequiredMixin, generic.ListView):
    """Список материалов с поиском и фильтрацией по категории."""

    model = Material
    template_name = 'materials/material_list.html'
    context_object_name = 'materials'
    paginate_by = 9

    def get_queryset(self):
        """Фильтрует материалы по видимости, поиску и категории."""
        user = self.request.user
        queryset = Material.objects.select_related('category', 'author').prefetch_related('tags')

        if not getattr(user, 'is_teacher', False):
            # Студент видит только публичные материалы и собственные.
            queryset = queryset.filter(
                Q(visibility=Material.Visibility.PUBLIC) | Q(author=user)
            ).filter(Q(is_published=True) | Q(author=user))

        search = self.request.GET.get('q', '').strip()
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(tags__name__icontains=search)
            ).distinct()

        category_slug = self.request.GET.get('category', '').strip()
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        return queryset

    def get_context_data(self, **kwargs):
        """Добавляет справочники и текущие параметры фильтра."""
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['search_query'] = self.request.GET.get('q', '')
        context['current_category'] = self.request.GET.get('category', '')
        return context


class MaterialDetailView(LoginRequiredMixin, generic.DetailView):
    """Детальная страница материала с проверкой прав."""

    model = Material
    template_name = 'materials/material_detail.html'
    context_object_name = 'material'

    def get_object(self, queryset=None):
        """Возвращает объект или выбрасывает 403 при отсутствии прав."""
        material = super().get_object(queryset)
        if not material.can_view(self.request.user):
            raise PermissionDenied('Нет прав на просмотр этого материала.')
        return material


class MaterialCreateView(LoginRequiredMixin, generic.CreateView):
    """Загрузка нового учебного материала."""

    model = Material
    form_class = MaterialForm
    template_name = 'materials/material_form.html'
    success_url = reverse_lazy('materials:list')

    def form_valid(self, form):
        """Назначает автора и сохраняет материал."""
        form.instance.author = self.request.user
        messages.success(self.request, 'Материал успешно загружен.')
        return super().form_valid(form)


class MaterialUpdateView(AuthorOrTeacherMixin, generic.UpdateView):
    """Редактирование материала автором или преподавателем."""

    model = Material
    form_class = MaterialForm
    template_name = 'materials/material_form.html'

    def form_valid(self, form):
        """Сохраняет изменения и выводит сообщение."""
        messages.success(self.request, 'Изменения сохранены.')
        return super().form_valid(form)


class MaterialDeleteView(AuthorOrTeacherMixin, generic.DeleteView):
    """Удаление материала автором или преподавателем."""

    model = Material
    template_name = 'materials/material_confirm_delete.html'
    success_url = reverse_lazy('materials:list')

    def form_valid(self, form):
        """Удаляет запись и выводит сообщение."""
        messages.warning(self.request, 'Материал удалён.')
        return super().form_valid(form)


class CategoryCreateView(TeacherRequiredMixin, generic.CreateView):
    """Создание категории (только преподаватель)."""

    model = Category
    form_class = CategoryForm
    template_name = 'materials/category_form.html'
    success_url = reverse_lazy('materials:list')

    def form_valid(self, form):
        """Сохраняет категорию и уведомляет пользователя."""
        messages.success(self.request, 'Категория создана.')
        return super().form_valid(form)


class CategoryUpdateView(TeacherRequiredMixin, generic.UpdateView):
    """Редактирование категории (только преподаватель)."""

    model = Category
    form_class = CategoryForm
    template_name = 'materials/category_form.html'
    success_url = reverse_lazy('materials:list')

    def form_valid(self, form):
        """Сохраняет изменения категории."""
        messages.success(self.request, 'Категория обновлена.')
        return super().form_valid(form)


class CategoryDeleteView(TeacherRequiredMixin, generic.DeleteView):
    """Удаление категории с обработкой PROTECT-связи."""

    model = Category
    template_name = 'materials/category_confirm_delete.html'
    success_url = reverse_lazy('materials:list')

    def form_valid(self, form):
        """Не позволяет удалить категорию, к которой привязаны материалы."""
        try:
            return super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                'Нельзя удалить категорию: к ней привязаны учебные материалы.',
            )
            return redirect('materials:list')


def _get_client_ip(request) -> str | None:
    """Извлекает IP-адрес клиента из запроса."""
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')



@login_required
def download_material(request, pk: int):
    """Скачивание файла с проверкой прав и записью в журнал."""
    material = get_object_or_404(Material, pk=pk)

    if not material.can_view(request.user):
        raise PermissionDenied('Нет прав на скачивание этого материала.')

    DownloadLog.objects.create(
        material=material,
        user=request.user,
        ip_address=_get_client_ip(request),
    )
    Material.objects.filter(pk=material.pk).update(
        downloads_count=F('downloads_count') + 1,
    )

    filename = os.path.basename(material.file.name)
    return FileResponse(
        material.file.open('rb'),
        as_attachment=True,
        filename=filename,
    )