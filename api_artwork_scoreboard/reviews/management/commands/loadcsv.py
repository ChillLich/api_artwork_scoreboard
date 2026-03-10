import csv
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from reviews.models import Category, Comment, Genre, Review, Title

User = get_user_model()


class Command(BaseCommand):
    help = "Импортирует данные из CSV файлов"

    def add_arguments(self, parser):
        parser.add_argument("--path", type=str, default="static/data", help="Путь к папке с CSV")

    def handle(self, *args, **options):
        base_path = options["path"]
        if not os.path.isabs(base_path):
            import django
            from django.conf import settings

            base_path = os.path.join(settings.BASE_DIR, base_path)

        if not os.path.exists(base_path):
            raise CommandError(f"Папка {base_path} не найдена")

        self.stdout.write("Начало импорта...")

        try:
            with transaction.atomic():
                self.import_categories(os.path.join(base_path, "category.csv"))
                self.import_genres(os.path.join(base_path, "genre.csv"))
                self.import_users(os.path.join(base_path, "users.csv"))
                self.import_titles(os.path.join(base_path, "titles.csv"))
                self.import_genre_title(os.path.join(base_path, "genre_title.csv"))
                self.import_reviews(os.path.join(base_path, "review.csv"))
                self.import_comments(os.path.join(base_path, "comments.csv"))

            self.stdout.write(self.style.SUCCESS("Успешно импортировано!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка импорта: {e}"))
            raise CommandError("Импорт отменен из-за ошибки")

    def read_csv(self, filepath):
        if not os.path.exists(filepath):
            self.stdout.write(self.style.WARNING(f"Файл {filepath} не найден, пропускаем"))
            return []
        with open(filepath, "r", encoding="utf-8") as f:
            data = list(csv.DictReader(f))
            if not data:
                self.stdout.write(
                    self.style.NOTICE(f"Файл {filepath} пуст или не прочитан, пропускаем")
                )
            return data

    def import_categories(self, path):
        data = self.read_csv(path)
        if not data:
            return
        objs = [Category(id=row["id"], name=row["name"], slug=row["slug"]) for row in data]
        Category.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f"Категории: {len(objs)}")

    def import_genres(self, path):
        data = self.read_csv(path)
        if not data:
            return
        objs = [Genre(id=row["id"], name=row["name"], slug=row["slug"]) for row in data]
        Genre.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f"Жанры: {len(objs)}")

    def import_users(self, path):
        data = self.read_csv(path)
        if not data:
            return
        users = []
        for row in data:
            user = User(
                id=row["id"],
                username=row["username"],
                email=row["email"],
                role=row["role"],
                bio=row.get("bio", ""),
                first_name=row.get("first_name", ""),
                last_name=row.get("last_name", ""),
            )
            user.set_unusable_password()
            users.append(user)
        User.objects.bulk_create(users, ignore_conflicts=True)
        self.stdout.write(f"Пользователи: {len(users)}")

    def import_titles(self, path):
        data = self.read_csv(path)
        if not data:
            return
        # получить объекты категорий для FK
        cats = {c.id: c for c in Category.objects.all()}
        objs = []
        for row in data:
            cat = cats.get(int(row["category"]))
            objs.append(
                Title(
                    id=row["id"],
                    name=row["name"],
                    year=row["year"],
                    category=cat,
                )
            )
        Title.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f"Произведения: {len(objs)}")

    def import_genre_title(self, path):
        """Обработка ManyToMany связи"""
        data = self.read_csv(path)
        if not data:
            return
        titles = {t.id: t for t in Title.objects.all()}
        genres = {g.id: g for g in Genre.objects.all()}

        count = 0
        for row in data:
            title = titles.get(int(row["title_id"]))
            genre = genres.get(int(row["genre_id"]))
            if title and genre:
                title.genre.add(genre)
                count += 1
        self.stdout.write(f"Связи жанров: {count}")

    def import_reviews(self, path):
        data = self.read_csv(path)
        if not data:
            return
        titles = {t.id: t for t in Title.objects.all()}
        users = {u.id: u for u in User.objects.all()}
        objs = []
        for row in data:

            objs.append(
                Review(
                    id=row["id"],
                    title=titles.get(int(row["title_id"])),
                    author=users.get(int(row["author"])),
                    text=row["text"],
                    score=row["score"],
                    pub_date=row["pub_date"],
                )
            )

        created = self.process_pub_date_field(Review, objs)

        self.stdout.write(f"Отзывы: {len(created)}")

    def import_comments(self, path):
        data = self.read_csv(path)
        if not data:
            return
        reviews = {r.id: r for r in Review.objects.all()}
        users = {u.id: u for u in User.objects.all()}
        objs = []
        for row in data:
            objs.append(
                Comment(
                    id=row["id"],
                    review=reviews.get(int(row["review_id"])),
                    author=users.get(int(row["author"])),
                    text=row["text"],
                    pub_date=row["pub_date"],
                )
            )

        created = self.process_pub_date_field(Comment, objs)

        self.stdout.write(f"Комментарии: {len(created)}")

    def process_pub_date_field(self, model, objs):
        """
        pub_date с auto_now_add=True может перезаписаться на текущее время
        Для сохранения исторической даты нужно временно отключить auto_now_add
        """
        date_field = model._meta.get_field("pub_date")
        original_field_value = date_field.auto_now_add
        date_field.auto_now_add = False
        try:
            created = model.objects.bulk_create(objs, ignore_conflicts=True)
        finally:
            date_field.auto_now_add = original_field_value
        return created
