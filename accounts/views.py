"""Представления регистрации, входа и выхода."""
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import generic
from django.views.decorators.http import require_POST

from .forms import RegisterForm


class RegisterView(generic.CreateView):
    """Регистрация нового пользователя с автоматическим входом."""

    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('materials:list')

    def dispatch(self, request, *args, **kwargs):
        """Авторизованному пользователю регистрация не нужна."""
        if request.user.is_authenticated:
            return redirect('materials:list')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Сохраняет пользователя, выполняет вход и выводит сообщение."""
        response = super().form_valid(form)
        auth_login(
            self.request,
            self.object,
            backend='django.contrib.auth.backends.ModelBackend',
        )
        messages.success(
            self.request,
            f'Добро пожаловать, {self.object.username}! Аккаунт успешно создан.',
        )
        return response


class LoginView(auth_views.LoginView):
    """Страница входа в систему."""

    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        """Добавляет приветственное сообщение после успешного входа."""
        messages.success(self.request, 'Вы успешно вошли в систему.')
        return super().form_valid(form)


@require_POST
def logout_view(request):
    """Выход из системы (только POST — защита от CSRF-подделки ссылок)."""
    auth_logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('materials:list')