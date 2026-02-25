import re
from datetime import date

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from rest_framework import serializers
from reviews.models import Category, Genre, Title

User = get_user_model()


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    username = serializers.CharField(max_length=150)

    def validate_username(self, value):
        if value.lower() == "me":
            raise serializers.ValidationError('Использовать имя "me" запрещено.')
        if not re.match(r"^[\w.@+-]+$", value):
            raise serializers.ValidationError("Недопустимые символы в username.")
        return value

    def validate(self, data):
        email = data.get("email")
        username = data.get("username")

        # Проверка уникальности пары email/username
        # Лучше отдавать унифицированное сообщение, чтобы защитить от перебора
        # который позволит узнавать email пользователей и соотносить с username
        if User.objects.filter(email=email).exclude(username=username).exists():
            raise serializers.ValidationError(
                {"email-username": "Пользователь с такими данными уже существует"}
            )
        if User.objects.filter(username=username).exclude(email=email).exists():
            raise serializers.ValidationError(
                {"email-username": "Пользователь с такими данными уже существует"}
            )
        return data


class TokenSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    confirmation_code = serializers.CharField()

    def validate(self, data):
        username = data.get("username")
        code = data.get("confirmation_code")

        signer = TimestampSigner()
        try:
            max_age = getattr(settings, "CONFIRMATION_CODE_EXPIRY_SECONDS", 86400)
            signed_data = signer.unsign_object(code, max_age=max_age)
        except (BadSignature, SignatureExpired):
            raise serializers.ValidationError("Неверный или просроченный код подтверждения.")

        email = signed_data.get("email")
        signed_username = signed_data.get("username")
        if not email or not signed_username:
            raise serializers.ValidationError("Неверный формат кода подтверждения.")

        if signed_username != username:
            raise serializers.ValidationError(
                "Неверный код подтверждения для данного пользователя."
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Пользователь не найден.")

        if user.username != username:
            raise serializers.ValidationError("Неверный username для данного email.")

        data["user"] = user
        return data


class CategoryGenreSerializerMixin(serializers.ModelSerializer):
    def validate_slug(self, value):
        if not re.match(r"^[-a-zA-Z0-9_]+$", value):
            raise serializers.ValidationError(
                "Slug может содержать только латинские буквы, цифры, дефис и подчёркивание."
            )
        return value


class CategorySerializer(CategoryGenreSerializerMixin):
    class Meta:
        model = Category
        fields = ("name", "slug")


class GenreSerializer(CategoryGenreSerializerMixin):
    class Meta:
        model = Genre
        fields = ("name", "slug")


class TitleReadSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(many=True, read_only=True)
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Title
        fields = ("id", "name", "year", "rating", "description", "genre", "category")

    def get_rating(self, obj):
        if hasattr(obj, "rating") and obj.rating is not None:
            return round(obj.rating, 1)
        return None


class TitleWriteSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(slug_field="slug", queryset=Category.objects.all())
    genre = serializers.SlugRelatedField(slug_field="slug", queryset=Genre.objects.all(), many=True)
    description = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Title
        fields = ("id", "name", "year", "description", "genre", "category")

    def validate_year(self, value):
        current_year = date.today().year
        if value > current_year:
            raise serializers.ValidationError("Год выпуска не может быть больше текущего.")
        return value
