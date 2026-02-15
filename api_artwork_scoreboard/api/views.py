from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.signing import TimestampSigner
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import SignupSerializer, TokenSerializer

User = get_user_model()


class SignupView(generics.GenericAPIView):
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        username = serializer.validated_data["username"]

        user, created = User.objects.get_or_create(email=email, defaults={"username": username})

        if not created:
            if user.username != username:
                return Response(
                    {"username": ["Этот email уже зарегистрирован с другим username."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            user.set_unusable_password()
            user.save()

        # Генерация подписанного кода
        signer = TimestampSigner()
        data_to_sign = {"email": email, "username": username}
        confirmation_code = signer.sign_object(data_to_sign)

        send_mail(
            subject="Код подтверждения",
            message=f"Ваш код подтверждения: {confirmation_code}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return Response({"email": email, "username": username}, status=status.HTTP_200_OK)


class TokenView(generics.GenericAPIView):
    serializer_class = TokenSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({"token": access_token})
