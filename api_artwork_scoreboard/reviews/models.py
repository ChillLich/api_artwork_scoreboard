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
