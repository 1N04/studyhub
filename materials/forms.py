"""Формы для работы с материалами и категориями."""
from django import forms

from .models import Category, Material


class MaterialForm(forms.ModelForm):
    """Форма загрузки и редактирования учебного материала."""

    class Meta:
        model = Material
        fields = ('title', 'description', 'category', 'file', 'visibility', 'tags')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'tags': forms.CheckboxSelectMultiple(),
        }

    def clean_title(self) -> str:
        """Проверяет осмысленность названия."""
        title = self.cleaned_data['title'].strip()
        if len(title) < 3:
            raise forms.ValidationError('Название должно содержать не менее 3 символов.')
        return title

    def clean(self):
        """Запрещает дублирование названий у одного автора."""
        cleaned_data = super().clean()
        title = cleaned_data.get('title')
        if title and self.instance.author_id:
            duplicates = Material.objects.filter(
                author_id=self.instance.author_id, title__iexact=title,
            ).exclude(pk=self.instance.pk)
            if duplicates.exists():
                self.add_error(
                    'title',
                    'У вас уже есть материал с таким названием.',
                )
        return cleaned_data


class CategoryForm(forms.ModelForm):
    """Форма создания и редактирования категории (доступна преподавателям)."""

    class Meta:
        model = Category
        fields = ('name', 'description')
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

    def clean_name(self) -> str:
        """Проверяет длину названия категории."""
        name = self.cleaned_data['name'].strip()
        if len(name) < 2:
            raise forms.ValidationError('Название категории слишком короткое.')
        return name