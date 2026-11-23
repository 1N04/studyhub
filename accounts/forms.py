"""Формы регистрации пользователей."""
from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class RegisterForm(UserCreationForm):
    """Форма регистрации с выбором роли и указанием группы."""

    email = forms.EmailField(label='Электронная почта', required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'group_name', 'password1', 'password2')
        labels = {
            'username': 'Логин',
            'role': 'Роль',
            'group_name': 'Учебная группа',
        }
        widgets = {
            'group_name': forms.TextInput(attrs={'placeholder': 'ПОВТ-1-24'}),
        }

    def clean_email(self) -> str:
        """Проверяет уникальность адреса электронной почты."""
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Пользователь с такой почтой уже зарегистрирован.')
        return email

    def clean_username(self) -> str:
        """Проверяет минимальную длину и допустимые символы логина."""
        username = self.cleaned_data['username'].strip()
        if len(username) < 3:
            raise forms.ValidationError('Логин должен содержать не менее 3 символов.')
        return username