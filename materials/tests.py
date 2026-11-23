"""Тесты CRUD материалов, прав доступа и скачивания файлов."""
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Category, DownloadLog, Material

User = get_user_model()


def make_file(name: str = 'lecture.pdf') -> SimpleUploadedFile:
    """Формирует тестовый файл допустимого формата."""
    return SimpleUploadedFile(name, b'%PDF-1.4 demo content', content_type='application/pdf')


class MaterialTestBase(TestCase):
    """Общая настройка: временный MEDIA_ROOT и набор пользователей."""

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
        self.other_student = User.objects.create_user('student2', password='StrongPass123')
        self.category = Category.objects.create(name='Математика')
        self.material = Material.objects.create(
            title='Лекция 1. Введение',
            description='Базовые понятия',
            file=make_file(),
            category=self.category,
            author=self.student,
            visibility=Material.Visibility.PUBLIC,
        )


class MaterialCrudTests(MaterialTestBase):
    """Сценарии создания, редактирования и удаления материалов."""

    def test_create_material_assigns_current_user_as_author(self):
        """При загрузке автором становится текущий пользователь."""
        self.client.login(username='student1', password='StrongPass123')
        response = self.client.post(reverse('materials:create'), {
            'title': 'Практика 1',
            'description': 'Задания',
            'category': self.category.pk,
            'visibility': Material.Visibility.PUBLIC,
            'file': make_file('practice.pdf'),
        })

        self.assertRedirects(response, reverse('materials:list'))
        created = Material.objects.get(title='Практика 1')
        self.assertEqual(created.author, self.student)

    def test_short_title_is_rejected_by_form(self):
        """Слишком короткое название не проходит валидацию формы."""
        self.client.login(username='student1', password='StrongPass123')
        response = self.client.post(reverse('materials:create'), {
            'title': 'ab',
            'description': 'Описание',
            'category': self.category.pk,
            'visibility': Material.Visibility.PUBLIC,
            'file': make_file('short.pdf'),
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'не менее 3 символов')
        self.assertFalse(Material.objects.filter(title='ab').exists())

    def test_author_can_update_own_material(self):
        """Автор может редактировать свой материал."""
        self.client.login(username='student1', password='StrongPass123')
        response = self.client.post(
            reverse('materials:update', args=[self.material.pk]),
            {
                'title': 'Лекция 1. Обновлено',
                'description': 'Новое описание',
                'category': self.category.pk,
                'visibility': Material.Visibility.PUBLIC,
                'file': make_file(),
            },
        )

        self.assertRedirects(
            response,
            reverse('materials:detail', args=[self.material.pk]),
        )
        self.material.refresh_from_db()
        self.assertEqual(self.material.title, 'Лекция 1. Обновлено')

    def test_other_student_cannot_update_foreign_material(self):
        """Чужой материал недоступен для редактирования — 403."""
        self.client.login(username='student2', password='StrongPass123')
        response = self.client.get(reverse('materials:update', args=[self.material.pk]))
        self.assertEqual(response.status_code, 403)

    def test_teacher_can_delete_foreign_material(self):
        """Преподаватель может модерировать и удалять чужие материалы."""
        self.client.login(username='teacher1', password='StrongPass123')
        response = self.client.post(reverse('materials:delete', args=[self.material.pk]))
        self.assertRedirects(response, reverse('materials:list'))
        self.assertFalse(Material.objects.filter(pk=self.material.pk).exists())


class MaterialAccessTests(MaterialTestBase):
    """Сценарии разграничения доступа и скачивания."""

    def test_private_material_download_forbidden_for_other_student(self):
        """Приватный материал не скачивается посторонним студентом."""
        self.material.visibility = Material.Visibility.PRIVATE
        self.material.save()

        self.client.login(username='student2', password='StrongPass123')
        response = self.client.get(reverse('materials:download', args=[self.material.pk]))

        self.assertEqual(response.status_code, 403)
        self.assertEqual(DownloadLog.objects.count(), 0)

    def test_public_material_download_allowed_and_logged(self):
        """Публичный материал скачивается, счётчик и журнал обновляются."""
        self.client.login(username='student2', password='StrongPass123')
        response = self.client.get(reverse('materials:download', args=[self.material.pk]))

        self.assertEqual(response.status_code, 200)
        self.material.refresh_from_db()
        self.assertEqual(self.material.downloads_count, 1)
        self.assertEqual(DownloadLog.objects.filter(material=self.material).count(), 1)

    def test_teacher_material_hidden_from_students(self):
        """Материал «только для преподавателей» недоступен постороннему студенту."""
        self.material.visibility = Material.Visibility.TEACHERS
        self.material.save()

        self.client.login(username='student2', password='StrongPass123')  # не автор
        response = self.client.get(reverse('materials:detail', args=[self.material.pk]))
        self.assertEqual(response.status_code, 403)

    def test_search_filters_materials_by_title(self):
        """Поиск по названию возвращает только совпадающие записи."""
        Material.objects.create(
            title='Лабораторная работа 5',
            file=make_file('lab5.pdf'),
            category=self.category,
            author=self.student,
        )
        self.client.login(username='student1', password='StrongPass123')
        response = self.client.get(reverse('materials:list'), {'q': 'Лабораторная'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Лабораторная работа 5')
        self.assertNotContains(response, 'Лекция 1. Введение')