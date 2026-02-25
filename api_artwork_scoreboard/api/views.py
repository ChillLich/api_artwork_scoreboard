from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.signing import TimestampSigner
from django.db.models import Avg
from django_filters.rest_framework import (
    CharFilter,
    DjangoFilterBackend,
    FilterSet,
    NumberFilter,
)
from rest_framework import filters, generics, mixins, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from reviews.models import Category, Genre, Title

from .permissions import IsAdminOrReadOnly
from .serializers import (
    CategorySerializer,
    GenreSerializer,
    SignupSerializer,
    TitleReadSerializer,
    TitleWriteSerializer,
    TokenSerializer,
)

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


class CategoryGenreViewSetMixin(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    lookup_field = "slug"
    search_fields = ("name",)
    ordering = ("name",)


class CategoryViewSet(CategoryGenreViewSetMixin):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class GenreViewSet(CategoryGenreViewSetMixin):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class TitleFilter(FilterSet):
    genre = CharFilter(field_name="genre__slug")
    category = CharFilter(field_name="category__slug")
    year = NumberFilter(field_name="year")
    name = CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = Title
        fields = ["genre", "category", "year", "name"]


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all().prefetch_related("genre", "category")
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = TitleFilter
    ordering_fields = ("name", "year")
    ordering = ("name",)

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return TitleReadSerializer
        return TitleWriteSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ("list", "retrieve"):
            return queryset.annotate(rating=Avg("reviews__score"))
        return queryset

    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
