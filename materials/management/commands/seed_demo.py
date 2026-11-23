"""Команда наполнения базы демонстрационными данными."""
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from materials.models import Category, Material, Tag

User = get_user_model()

CATEGORIES = [
    ('Математика', 'Алгебра, геометрия, математический анализ'),
    ('Программирование', 'Алгоритмы, языки программирования, практикумы'),
    ('Базы данных', 'SQL, проектирование и нормализация схем'),
    ('Иностранные языки', 'Английский язык для ИТ-специальностей'),
]

TAGS = ['лекция', 'практика', 'конспект', 'экзамен', 'методичка']

MATERIALS = [
    ('Конспект лекций по дискретной математике', 'Математика',
     'Основные определения, операции над множествами, булева алгебра.', 'public', 'лекция'),
    ('Практикум по алгоритмам сортировки', 'Программирование',
     'Разбор быстрой сортировки и сортировки слиянием, анализ сложности.', 'public', 'практика'),
    ('Методичка по проектированию БД', 'Базы данных',
     'Нормальные формы, ER-диаграммы, примеры проектирования.', 'public', 'методичка'),
    ('Варианты экзаменационных заданий', 'Программирование',
     'Закрытые задания и задачи с развёрнутым ответом.', 'teachers', 'экзамен'),
    ('Личный конспект по SQL-запросам', 'Базы данных',
     'JOIN-ы, подзапросы, оконные функции.', 'private', 'конспект'),
    ('English for IT: Unit 1', 'Иностранные языки',
     'Профессиональная лексика, упражнения на перевод.', 'public', 'практика'),
]


class Command(BaseCommand):
    """Создаёт демо-пользователей, категории, теги и материалы."""

    help = 'Наполняет базу демонстрационными данными для защиты курсовой работы.'

    def add_arguments(self, parser):
        """Добавляет флаг сброса существующих материалов."""
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Удалить существующие материалы перед наполнением.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        """Выполняет наполнение базы."""
        if options['reset']:
            Material.objects.all().delete()
            self.stdout.write(self.style.WARNING('Существующие материалы удалены.'))

        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@studyhub.local',
                'role': User.Role.TEACHER,
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if created:
            admin.set_password('admin12345')
            admin.save()
            self.stdout.write(self.style.SUCCESS('Создан суперпользователь admin / admin12345'))

        teachers = []
        for username in ('teacher1', 'teacher2'):
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'role': User.Role.TEACHER, 'email': f'{username}@studyhub.local'},
            )
            if created:
                user.set_password('Passw0rd!')
                user.save()
            teachers.append(user)

        students = []
        for index, username in enumerate(('student1', 'student2'), start=1):
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'role': User.Role.STUDENT,
                    'email': f'{username}@studyhub.local',
                    'group_name': 'ПОВТ-1-24',
                },
            )
            if created:
                user.set_password('Passw0rd!')
                user.save()
            students.append(user)

        categories = {}
        for name, description in CATEGORIES:
            category, _ = Category.objects.get_or_create(
                name=name, defaults={'description': description},
            )
            categories[name] = category

        tags = {name: Tag.objects.get_or_create(name=name)[0] for name in TAGS}

        created_count = 0
        for index, (title, category_name, description, visibility, tag_name) in enumerate(MATERIALS):
            if Material.objects.filter(title=title).exists():
                continue
            author = students[index % len(students)]
            material = Material(
                title=title,
                description=description,
                category=categories[category_name],
                author=author,
                visibility=visibility,
            )
            content = f'Демонстрационный файл материала «{title}».\n'.encode('utf-8')
            material.file.save(f'demo_{index + 1}.txt', ContentFile(content), save=False)
            material.save()
            material.tags.add(tags[tag_name])
            created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Готово. Категорий: {Category.objects.count()}, '
            f'материалов: {Material.objects.count()} (создано сейчас: {created_count}).'
        ))
        self.stdout.write(self.style.SUCCESS('Учётные записи: admin/admin12345, '
                                             'teacher1/Passw0rd!, student1/Passw0rd!, student2/Passw0rd!'))