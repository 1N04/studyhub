# StudyHub — платформа обмена учебными материалами

Курсовой проект по дисциплине «Компьютерное моделирование»
(КОМТЕХНО, 3 курс, 2026). Тема №4: загрузка, категоризация и скачивание
файлов с правами доступа.

## Стек

* Python 3.11+
* Django 5.0.6 (MVT, ORM, SQLite)
* Django REST Framework 3.15.1
* python-decouple 3.8 (хранение секретов в `.env`)

## Быстрый старт

```bash
python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env              # Windows: copy .env.example .env

python manage.py makemigrations accounts materials
python manage.py migrate
python manage.py seed_demo        # демо-данные + суперпользователь
python manage.py runserver
```

Приложение доступно по адресу <http://127.0.0.1:8000/>.

## Демонстрационные учётные записи

| Логин | Пароль | Роль |
|---|---|---|
| `admin` | `admin12345` | суперпользователь / преподаватель |
| `teacher1` | `Passw0rd!` | преподаватель |
| `student1` | `Passw0rd!` | студент |
| `student2` | `Passw0rd!` | студент |

Админ-панель: <http://127.0.0.1:8000/admin/>.

## Команды

```bash
python manage.py migrate              # применить миграции
python manage.py makemigrations       # создать миграции после правок моделей
python manage.py seed_demo            # наполнить БД демо-данными
python manage.py seed_demo --reset    # удалить материалы и наполнить заново
python manage.py createsuperuser      # создать администратора вручную
python manage.py test                 # запустить автотесты
python manage.py collectstatic        # собрать статику (production)
```

## Роли и права

| Действие | Студент | Преподаватель |
|---|---|---|
| Просмотр публичных материалов | ✅ | ✅ |
| Просмотр материалов «только преподавателям» | ❌ | ✅ |
| Просмотр своего приватного материала | ✅ | ✅ |
| Просмотр чужого приватного материала | ❌ | ✅ |
| Загрузка материалов | ✅ | ✅ |
| Редактирование/удаление своего материала | ✅ | ✅ |
| Редактирование/удаление чужого материала | ❌ | ✅ |
| Создание/редактирование категорий | ❌ | ✅ |
| Модерация (снятие с публикации) | ❌ | ✅ (админка) |
| Журнал скачиваний материала | только своего | любой |

## REST API

Базовый префикс: `/api/`. Аутентификация — сессия (Browsable API) или Basic Auth.
Все эндпоинты требуют аутентификации.

| Метод | URL | Назначение |
|---|---|---|
| GET | `/api/categories/` | Список категорий |
| GET | `/api/materials/` | Список доступных материалов (`?search=`, `?category=<slug>`) |
| POST | `/api/materials/` | Создание материала (multipart/form-data) |
| GET | `/api/materials/<id>/` | Детальная информация |
| PATCH/PUT | `/api/materials/<id>/` | Изменение (автор или преподаватель) |
| DELETE | `/api/materials/<id>/` | Удаление (автор или преподаватель) |
| GET | `/api/materials/<id>/downloads/` | Журнал скачиваний (автор или преподаватель) |

Пример создания материала:

```bash
curl -u student1:Passw0rd! -X POST http://127.0.0.1:8000/api/materials/ \
  -F "title=Конспект лекции" \
  -F "category=1" \
  -F "visibility=public" \
  -F "file=@lecture.pdf"
```

## Структура проекта

```
config/     — настройки, корневые маршруты
accounts/   — пользователь с ролью, регистрация/вход/выход
materials/  — Category, Tag, Material, DownloadLog, CRUD, шаблоны
api/        — сериализаторы, permissions, DRF-эндпоинты
templates/  — HTML-шаблоны
static/     — CSS
media/      — загруженные пользователями файлы
```

## Безопасность

* Секреты — только в `.env` (python-decouple), файл в `.gitignore`.
* Все браузерные формы защищены CSRF-токеном (`{% csrf_token %}`).
* Выход реализован только через POST.
* Валидация типов и размера файлов (`materials/validators.py`).
* Разграничение доступа на уровне моделей (`can_view`, `can_edit`),
  представлений и DRF-permissions.
* Кастомные страницы 403/404/500.

## Тестирование

```bash
python manage.py test
```

16 автотестов покрывают регистрацию/вход, CRUD материалов, права ролей,
скачивание файлов, работу REST API (200/201/204/403).