# Artwork Scoreboard API

API для проекта **api_artwork_scoreboard** - платформа для сбора отзывов пользователей на произведения (книги, фильмы, музыку и др.).

## Описание

Проект предоставляет REST API для:

- Регистрации и аутентификации пользователей (JWT-токены)
- Управления произведениями, категориями и жанрами
- Публикации отзывов и комментариев
- Выставления оценок и расчёта рейтинга произведений

## Технологии

- Python 3.7+
- Django 3.2+
- Django REST Framework
- PyJWT - аутентификация

## Быстрый старт

### Клонирование репозитория

```bash
git clone git@github.com:ChillLich/api_artwork_scoreboard.git
cd api_artwork_scoreboard
```

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Применение миграций

```bash
python manage.py migrate
```

### Загрузка данных из CSV (опционально)

```bash
python manage.py loadcsv
```

### Запуск сервера

```bash
python manage.py runserver
```

API доступно по адресу: `http://127.0.0.1:8000/api/v1/`

Документация: `http://127.0.0.1:8000/redoc/`

## Основные эндпоинты

| Ресурс | Эндпоинт |
|--------|----------|
| Аутентификация | `/api/v1/auth/signup/`, `/api/v1/auth/token/` |
| Пользователи | `/api/v1/users/`, `/api/v1/users/me/` |
| Произведения | `/api/v1/titles/` |
| Категории | `/api/v1/categories/` |
| Жанры | `/api/v1/genres/` |
| Отзывы | `/api/v1/titles/{id}/reviews/` |
| Комментарии | `/api/v1/titles/{title_id}/reviews/{review_id}/comments/` |

## Роли и права доступа

| Роль | Права |
|------|-------|
| **Аноним** | Просмотр произведений, отзывов, комментариев |
| **User** | + создание отзывов, комментариев, оценок |
| **Moderator** | + редактирование/удаление любых отзывов и комментариев |
| **Admin** | Полный доступ ко всем ресурсам |

## Тестирование

```bash
python -m pytest
```

## Импорт данных

Данные для наполнения БД находятся в `/static/data/`. Для импорта используется management-команда `loadcsv`.
