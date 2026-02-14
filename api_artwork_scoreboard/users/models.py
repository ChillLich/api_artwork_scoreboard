from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        # лучше так чем магическая строка в choices
        USER = "user", "user"
        MODERATOR = "moderator", "moderator"
        ADMIN = "admin", "admin"

    email = models.EmailField(unique=True)
    bio = models.TextField("Биография", blank=True)
    role = models.CharField(
        choices=Role.choices,
        max_length=256,
        default="user",
    )

    def save(self, *args, **kwargs):
        if self.role == self.Role.ADMIN:
            self.is_staff = True
        else:
            self.is_staff = False
        super().save(*args, **kwargs)
