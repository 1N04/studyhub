"""Тесты регистрации, входа и выхода."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class AuthTests(TestCase):
    """Проверка базовых сценариев аутентификации."""

    def test_register_creates_user_with_student_role(self):
        """Регистрация создаёт пользователя с ролью «студент» и входит в систему."""
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newstudent',
            'email': 'newstudent@example.com',
            'role': User.Role.STUDENT,
            'group_name': 'ПОВТ-1-24',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
        })

        self.assertRedirects(response, reverse('materials:list'))
        user = User.objects.get(username='newstudent')
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertTrue(user.check_password('StrongPass123'))
        # Пользователь автоматически авторизован
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_login_and_logout_flow(self):
        """Корректные учётные данные пускают в систему, выход завершает сессию."""
        User.objects.create_user('student1', password='StrongPass123')

        response = self.client.post(reverse('accounts:login'), {
            'username': 'student1',
            'password': 'StrongPass123',
        }, follow=True)
        # после follow итоговый ответ — 200 от MaterialListView
        self.assertEqual(response.status_code, 200)
        self.assertIn('_auth_user_id', self.client.session)

        response = self.client.post(reverse('accounts:logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_with_wrong_password_shows_error(self):
        """Неверный пароль не создаёт сессию."""
        User.objects.create_user('student1', password='StrongPass123')
        response = self.client.post(reverse('accounts:login'), {
            'username': 'student1',
            'password': 'WrongPass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)