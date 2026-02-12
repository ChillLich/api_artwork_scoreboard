from django.contrib.auth import get_user_model
from django.db import models


class Genre(models.Model):
    name = models.CharField("Название", max_length=256)
    slug = models.SlugField(max_length=50)


class Category(models.Model):
    name = models.CharField("Название", max_length=256)
    slug = models.SlugField(max_length=50)


class Title(models.Model):
    name = models.CharField("Название", max_length=256)
    year = models.IntegerField("Год выпуска")
    description = models.TextField("Описание")
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, related_name="titles")
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="titles"
    )
User = get_user_model()


class Review(models.Model):

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(score__gte=1, score__lte=10), name="score_range_1_to_10"
            )
        ]

    # TODO: Раскомментить как допишется Title и User
    # title = models.ForeignKey(Title, on_delete=models.CASCADE, related_name="reviews")
    # author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    text = models.TextField()
    score = models.PositiveSmallIntegerField(
        choices=[(i, str(i)) for i in range(1, 11)],
        help_text="Оценка от 1 до 10",
    )
    pub_date = models.DateTimeField(auto_now_add=True)
