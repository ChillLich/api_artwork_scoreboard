from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.signing import TimestampSigner
from django.db.models import Avg
from django.http import Http404
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import (
    CharFilter,
    DjangoFilterBackend,
    FilterSet,
    NumberFilter,
)
from rest_framework import filters, generics, mixins, permissions, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from reviews.models import Category, Comment, Genre, Review, Title

from . import serializers
from .permissions import IsAdminOrReadOnly, IsModerAuthorOrReadOnly

User = get_user_model()


class SignupView(generics.GenericAPIView):
    serializer_class = serializers.SignupSerializer
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
    serializer_class = serializers.TokenSerializer
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
    serializer_class = serializers.CategorySerializer


class GenreViewSet(CategoryGenreViewSetMixin):
    queryset = Genre.objects.all()
    serializer_class = serializers.GenreSerializer


class TitleFilter(FilterSet):
    genre = CharFilter(field_name="genre__slug")
    category = CharFilter(field_name="category__slug")
    year = NumberFilter(field_name="year")
    name = CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = Title
        fields = ["genre", "category", "year", "name"]


class TitleViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options", "trace"]
    queryset = Title.objects.all().prefetch_related("genre", "category")
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = TitleFilter
    ordering_fields = ("name", "year")
    ordering = ("name",)

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return serializers.TitleReadSerializer
        return serializers.TitleWriteSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ("list", "retrieve"):
            return queryset.annotate(rating=Avg("reviews__score"))
        return queryset


class ReviewViewset(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options", "trace"]
    permission_classes = (IsModerAuthorOrReadOnly,)
    serializer_class = serializers.ReviewSerializer

    def get_queryset(self):
        title_id = self.kwargs.get("title_id")
        if not Title.objects.filter(id=title_id).exists():
            raise Http404("Произведение не найдено")
        return Review.objects.filter(title_id=title_id)

    def perform_create(self, serializer):
        title_id = self.kwargs.get("title_id")
        title = get_object_or_404(Title, id=title_id)
        serializer.save(author=self.request.user, title=title)


class CommentReviewViewset(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options", "trace"]
    permission_classes = (IsModerAuthorOrReadOnly,)
    serializer_class = serializers.CommentReviewSerializer

    def get_queryset(self):
        review_id = self.kwargs.get("review_id")
        if not Review.objects.filter(id=review_id).exists():
            raise Http404("Отзыв не найден")
        return Comment.objects.filter(review_id=review_id)

    def perform_create(self, serializer):
        review_id = self.kwargs.get("review_id")
        review = get_object_or_404(Review, id=review_id)
        serializer.save(author=self.request.user, review=review)
