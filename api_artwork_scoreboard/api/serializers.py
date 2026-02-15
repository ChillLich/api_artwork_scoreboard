import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from rest_framework import serializers

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
