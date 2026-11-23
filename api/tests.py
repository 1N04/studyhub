"""Тесты REST API: аутентификация, права, создание и удаление."""
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from materials.models import Category, Material

User = get_user_model()


def make_file(name: str = 'api.pdf') -> SimpleUploadedFile:
    """Формирует тестовый файл для multipart-запроса."""
    return SimpleUploadedFile(name, b'%PDF-1.4 api content', content_type='application/pdf')


class ApiTestBase(APITestCase):
    """Общая настройка API-тестов."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._tmp_media = tempfile.mkdtemp()
        cls._media_override = override_settings(MEDIA_ROOT=cls._tmp_media)
        cls._media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls._media_override.disable()
        shutil.rmtree(cls._tmp_media, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.teacher = User.objects.create_user(
            'teacher1', password='StrongPass123', role=User.Role.TEACHER,
        )
        self.student = User.objects.create_user('student1', password='StrongPass123')
        self.other = User.objects.create_user('student2', password='StrongPass123')
        self.category = Category.objects.create(name='Программирование')
        self.material = Material.objects.create(
            title='API-материал',
            file=make_file(),
            category=self.category,
            author=self.student,
        )


class MaterialApiTests(ApiTestBase):
    """Проверка эндпоинтов /api/materials/."""

    def test_anonymous_access_denied(self):
        """Без аутентификации список материалов недоступен."""
        response = self.client.get('/api/materials/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_can_create_material(self):
        """Авторизованный пользователь создаёт материал через API (201)."""
        self.client.force_authenticate(self.student)
        payload = {
            'title': 'Новый API-материал',
            'description': 'Описание',
            'category': self.category.pk,
            'visibility': Material.Visibility.PUBLIC,
            'file': make_file('new.pdf'),
        }
        response = self.client.post('/api/materials/', payload, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Material.objects.get(title='Новый API-материал')
        self.assertEqual(created.author, self.student)
        self.assertEqual(response.data['author'], 'student1')

    def test_other_user_cannot_delete_material(self):
        """Студент не может удалить чужой материал — 403."""
        self.client.force_authenticate(self.other)
        response = self.client.delete(f'/api/materials/{self.material.pk}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Material.objects.filter(pk=self.material.pk).exists())

    def test_teacher_can_delete_material(self):
        """Преподаватель удаляет чужой материал — 204."""
        self.client.force_authenticate(self.teacher)
        response = self.client.delete(f'/api/materials/{self.material.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Material.objects.filter(pk=self.material.pk).exists())

    def test_private_material_not_visible_in_list(self):
        """Приватный материал не попадает в список постороннего пользователя."""
        self.material.visibility = Material.Visibility.PRIVATE
        self.material.save()

        self.client.force_authenticate(self.other)
        response = self.client.get('/api/materials/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)